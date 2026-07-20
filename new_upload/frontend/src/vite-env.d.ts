/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL: string;
  readonly VITE_APP_NAME: string;
  // Comma-separated admin app hostnames. When set, any other host is treated
  // as a school's custom domain and renders the public site at "/".
  readonly VITE_APP_HOSTS: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
