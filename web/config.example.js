/* Starter config — copy to config.js and fill from `terraform output`.
   deploy.sh prints these values after apply. */
window.APP_CONFIG = window.APP_CONFIG || {
  region: "ap-south-1",
  userPoolId: "REPLACE_ME",
  userPoolClientId: "REPLACE_ME",
  cognitoDomain: "REPLACE_ME.auth.ap-south-1.amazoncognito.com",
  apiEndpoint: "https://REPLACE_ME.execute-api.ap-south-1.amazonaws.com",
  redirectUri: window.location.origin + window.location.pathname,
};
