resource "helm_release" "external-dns" {
  name = "external-dns"
  namespace = "external-dns"
  version = "1.13.0"
  create_namespace = true
  wait = true
  repository = "https://kubernetes-sigs.github.io/external-dns/"
  chart = "external-dns"
  values = [
    <<-EOT
      logLevel: debug
      publishInternalServices: true
      extraVolumes:
        - name: aws-credentials
          secret:
            secretName: external-dns
      extraVolumeMounts:
        - name: aws-credentials
          mountPath: /.aws
          readOnly: true
      env:
        - name: AWS_SHARED_CREDENTIALS_FILE
          value: /.aws/credentials
    EOT
  ]
}
