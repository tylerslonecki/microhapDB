// main.js
import { createApp } from 'vue';
import App from './App.vue';
import router from './router'; 
import store from './store'; // Import the store

import PrimeVue from 'primevue/config';
import Menubar from 'primevue/menubar';
import PanelMenu from 'primevue/panelmenu';
import Button from 'primevue/button';
import InputText from 'primevue/inputtext';
import Dropdown from 'primevue/dropdown';
import DataTable from 'primevue/datatable';
import Column from 'primevue/column';
import Paginator from 'primevue/paginator';
import FileUpload from 'primevue/fileupload';
import ToastService from 'primevue/toastservice';
import Toast from 'primevue/toast';
import Tooltip from 'primevue/tooltip';
import ConfirmDialog from 'primevue/confirmdialog'; // Import ConfirmDialog
import ConfirmationService from 'primevue/confirmationservice';

// PrimeVue styles
import 'primevue/resources/themes/lara-light-green/theme.css';  
import 'primevue/resources/primevue.min.css';
import 'primeicons/primeicons.css';

// PrimeFlex
import 'primeflex/primeflex.css'; // Import PrimeFlex

// Import axios config to ensure it's loaded before any API calls
import './axiosConfig';

const app = createApp(App);
app.use(PrimeVue);
app.use(router);
app.use(store);
app.use(ToastService);
app.use(ConfirmationService);

app.component('Menubar', Menubar);
app.component('PanelMenu', PanelMenu);
app.component('Button', Button);
app.component('InputText', InputText);
app.component('Dropdown', Dropdown);
app.component('DataTable', DataTable);
app.component('Column', Column);
app.component('Paginator', Paginator);
app.component('FileUpload', FileUpload);
app.component('Toast', Toast);
app.component('ConfirmDialog', ConfirmDialog); // Register ConfirmDialog globally
app.directive('tooltip', Tooltip);

app.mount('#app');
