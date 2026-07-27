#!/usr/bin/env bash
set -euo pipefail

readonly hostname="sign.keeperfinancial.ca"
readonly output_dir="${1:-storage/local-documenso-tls}"
readonly system_bundle="/etc/ssl/certs/ca-certificates.crt"

if [[ ! -r "$system_bundle" ]]; then
  printf 'System CA bundle is unavailable: %s\n' "$system_bundle" >&2
  exit 1
fi

mkdir -p "$output_dir"
umask 077

for path in ca.key ca.crt server.key server.crt ca-bundle.crt; do
  if [[ -e "$output_dir/$path" ]]; then
    printf 'Refusing to overwrite existing local TLS material: %s\n' "$output_dir/$path" >&2
    exit 1
  fi
done

extensions="$(mktemp)"
trap 'rm -f "$extensions"' EXIT
cat >"$extensions" <<EOF
basicConstraints=critical,CA:FALSE
keyUsage=critical,digitalSignature,keyEncipherment
extendedKeyUsage=serverAuth
subjectAltName=DNS:${hostname}
EOF

openssl req -x509 -newkey rsa:3072 -sha256 -days 825 -nodes \
  -subj "/CN=Keeper Financial Local Development CA" \
  -addext "basicConstraints=critical,CA:TRUE" \
  -addext "keyUsage=critical,keyCertSign,cRLSign" \
  -keyout "$output_dir/ca.key" \
  -out "$output_dir/ca.crt"

openssl req -new -newkey rsa:3072 -sha256 -nodes \
  -subj "/CN=${hostname}" \
  -keyout "$output_dir/server.key" \
  -out "$output_dir/server.csr"

openssl x509 -req -sha256 -days 825 \
  -in "$output_dir/server.csr" \
  -CA "$output_dir/ca.crt" \
  -CAkey "$output_dir/ca.key" \
  -CAcreateserial \
  -extfile "$extensions" \
  -out "$output_dir/server.crt"

cp "$system_bundle" "$output_dir/ca-bundle.crt"
printf '\n' >>"$output_dir/ca-bundle.crt"
cat "$output_dir/ca.crt" >>"$output_dir/ca-bundle.crt"
rm -f "$output_dir/server.csr" "$output_dir/ca.srl"
chmod 600 "$output_dir/ca.key" "$output_dir/server.key"
chmod 644 "$output_dir/ca.crt" "$output_dir/server.crt" "$output_dir/ca-bundle.crt"

printf 'Generated local TLS material for %s in %s.\n' "$hostname" "$output_dir"
