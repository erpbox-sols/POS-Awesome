# Copyright (c) 2021, Youssef Restom and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, requests
from frappe import _
from requests.auth import HTTPBasicAuth
import json


def get_token(app_key, app_secret, base_url):
    authenticate_uri = "/oauth/v1/generate?grant_type=client_credentials"
    authenticate_url = "{0}{1}".format(base_url, authenticate_uri)

    r = requests.get(authenticate_url, auth=HTTPBasicAuth(app_key, app_secret))

    return r.json()["access_token"]

@frappe.whitelist()
def register_c2b_urls(
    shortcode: str,
    app_key: str,
    app_secret: str,
    base_url: str,
    validation_url: str,
    confirmation_url: str,
    response_type: str = "Completed"
):
    """
    Register or overwrite C2B URLs with Safaricom.
    Logs both request and response together in a single Error Log.
    """
    try:
        # get OAuth token
        token = get_token(app_key, app_secret, base_url)

        # endpoint
        register_url = f"{base_url}/mpesa/c2b/v1/registerurl"

        # request payload
        payload = {
            "ShortCode": shortcode,
            "ResponseType": response_type,
            "ConfirmationURL": confirmation_url,
            "ValidationURL": validation_url,
        }

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        # send request
        r = requests.post(register_url, json=payload, headers=headers, timeout=30)
        r.raise_for_status()

        # build combined log
        log_message = f"""
            M-PESA C2B Registration Attempt

            ▶️ Request:
            {json.dumps(payload, indent=2)}

            ▶️ Response:
            {r.text}
            """

        frappe.log_error(log_message, "M-PESA C2B Registration")

        return r.json()

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), f"M-Pesa C2B URL Registration Error: {str(e)[:140]}")
        return {"error": str(e)}


@frappe.whitelist(allow_guest=True)
def confirmation(**kwargs):
    try:
        args = frappe._dict(kwargs)
        doc = frappe.new_doc("Mpesa Payment Register")
        doc.transactiontype = args.get("TransactionType")
        doc.transid = args.get("TransID")
        doc.transtime = args.get("TransTime")
        doc.transamount = args.get("TransAmount")
        doc.businessshortcode = args.get("BusinessShortCode")
        doc.billrefnumber = args.get("BillRefNumber")
        doc.invoicenumber = args.get("InvoiceNumber")
        doc.orgaccountbalance = args.get("OrgAccountBalance")
        doc.thirdpartytransid = args.get("ThirdPartyTransID")
        doc.msisdn = args.get("MSISDN")
        doc.firstname = args.get("FirstName")
        doc.middlename = args.get("MiddleName")
        doc.lastname = args.get("LastName")
        doc.insert(ignore_permissions=True)
        frappe.db.commit()
        context = {"ResultCode": 0, "ResultDesc": "Accepted"}
        return dict(context)
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), str(e)[:140])
        context = {"ResultCode": 1, "ResultDesc": "Rejected"}
        return dict(context)


@frappe.whitelist(allow_guest=True)
def validation(**kwargs):
    context = {"ResultCode": 0, "ResultDesc": "Accepted"}
    return dict(context)


@frappe.whitelist()
def get_mpesa_mode_of_payment(company):
    modes = frappe.get_all(
        "Mpesa C2B Register URL",
        filters={"company": company, "register_status": "Success"},
        fields=["mode_of_payment"],
    )
    modes_of_payment = []
    for mode in modes:
        if mode.mode_of_payment not in modes_of_payment:
            modes_of_payment.append(mode.mode_of_payment)
    return modes_of_payment


@frappe.whitelist()
def get_mpesa_draft_payments(
    company,
    mode_of_payment=None,
    mobile_no=None,
    full_name=None,
    payment_methods_list=None,
):
    filters = {"company": company, "docstatus": 0}
    if mode_of_payment:
        filters["mode_of_payment"] = mode_of_payment
    if mobile_no:
        filters["msisdn"] = ["like", f"%{mobile_no}%"]
    if full_name:
        filters["full_name"] = ["like", f"%{full_name}%"]
    if payment_methods_list:
        filters["mode_of_payment"] = ["in", json.loads(payment_methods_list)]

    payments = frappe.get_all(
        "Mpesa Payment Register",
        filters=filters,
        fields=[
            "name",
            "transid",
            "msisdn as mobile_no",
            "full_name",
            "posting_date",
            "transamount as amount",
            "currency",
            "mode_of_payment",
            "company",
        ],
        order_by="posting_date desc",
    )
    return payments


@frappe.whitelist()
def submit_mpesa_payment(mpesa_payment, customer):
    doc = frappe.get_doc("Mpesa Payment Register", mpesa_payment)
    doc.customer = customer
    doc.submit_payment = 1
    doc.submit()
    doc.reload()
    return frappe.get_doc("Payment Entry", doc.payment_entry)
