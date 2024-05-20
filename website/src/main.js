
import { createApp } from 'vue'
import App from './App.vue'
import 'fetch-retry/dist/fetch-retry.umd.js'
import 'bootstrap/dist/css/bootstrap.css'
import 'bootstrap/dist/js/bootstrap.js'
import { Amplify } from 'aws-amplify';
import awsExports from './aws-exports';
Amplify.configure(awsExports);
createApp(App).mount('#app')

