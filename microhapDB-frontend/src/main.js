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

// PrimeVue styles
import 'primevue/resources/themes/lara-light-green/theme.css';  
import 'primevue/resources/primevue.min.css';
import 'primeicons/primeicons.css';

// PrimeFlex
import 'primeflex/primeflex.css'; // Import PrimeFlex

const app = createApp(App);
app.use(PrimeVue);
app.use(router);
app.use(store);

app.component('Menubar', Menubar);
app.component('PanelMenu', PanelMenu);
app.component('Button', Button);
app.component('InputText', InputText);
app.component('Dropdown', Dropdown);
app.component('DataTable', DataTable);
app.component('Column', Column);
app.component('Paginator', Paginator);
app.component('FileUpload', FileUpload);


app.mount('#app');
