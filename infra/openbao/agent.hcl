vault {
  address = "https://openbao.openbao.svc:8200"
}

auto_auth {
  method "kubernetes" {
    mount_path = "auth/kubernetes"
    config = {
      role = "agentic-ai-brief-runtime"
      token_path = "/var/run/secrets/kubernetes.io/serviceaccount/token"
    }
  }
}

api_proxy {
  use_auto_auth_token = "force"
}

listener "tcp" {
  address = "127.0.0.1:8100"
  tls_disable = true
}

template {
  destination = "/run/secrets/database_url"
  perms = "0400"
  contents = "{{ with secret \"kv/data/agentic-ai-brief/runtime\" }}{{ .Data.data.database_url }}{{ end }}"
  error_on_missing_key = true
}
