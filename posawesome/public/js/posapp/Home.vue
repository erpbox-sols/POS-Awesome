<template>
  <v-app class="container1">
    <v-main>
      <Navbar @changePage="setPage"></Navbar>
      <keep-alive>
        <component :is="page" class="mx-4 md-4" />
      </keep-alive>
    </v-main>
  </v-app>
</template>

<script>
import Navbar from './components/Navbar.vue';
import POS from './components/pos/Pos.vue';
import Payments from './components/payments/Pay.vue';

export default {
  name: "Home",
  components: {
    Navbar,
    POS,
    Payments,
  },
  data() {
    return {
      page: 'POS',
      frappeNavRemoved: false,
    };
  },
  methods: {
    setPage(page) {
      if (this.page !== page) {
        this.page = page;
      }
    },
    removeFrappeNav() {
      // Only remove once for performance
      if (this.frappeNavRemoved) return;
      this.frappeNavRemoved = true;
      this.$nextTick(() => {
        const head = document.querySelector('.page-head');
        if (head) head.remove();
        const nav = document.querySelector('.navbar.navbar-default.navbar-fixed-top');
        if (nav) nav.remove();
      });
    },
  },
  mounted() {
    this.removeFrappeNav();
  },
  created() {
     setTimeout(() => {
      this.removeFrappeNav();
    }, 500);
  },
};
</script>

<style scoped>
.container1 {
  margin-top: 0px;
}
</style>