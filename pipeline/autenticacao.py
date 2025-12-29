import requests


class APIClient:
    def __init__(self, usuario="dev.synthexa", senha="Dinamica@123"):
        self.usuario = usuario
        self.senha = senha
        self.token = None
        self.base_url = "https://rest.megaerp.online/api"
        self.tenant_id = "177a3ea9-cf41-42bb-85a3-5c11c3f08c63"

    def autenticar(self):
        url = f"{self.base_url}/Auth/SignIn"
        payload = {
            "UserName": self.usuario,
            "Password": self.senha
        }
        headers = {
            "Content-Type": "application/json",
            "TenantId": self.tenant_id
        }

        response = requests.post(url, json=payload, headers=headers)

        if response.status_code == 200:
            data = response.json()
            self.token = data.get("accessToken")
            if not self.token:
                raise Exception(f"AccessToken não encontrado na resposta: {data}")
            return self.token
        else:
            raise Exception(f"Falha na autenticação: {response.status_code} - {response.text}")

    def _get_headers(self):
        if not self.token:
            self.autenticar()

        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}",
            "TenantId": self.tenant_id
        }

    def get_produtos(self, filtros=None):
        headers = self._get_headers()
        url = f"{self.base_url}/produto/Produto"

        if filtros:
            url += "?" + "&".join([f"{k}={v}" for k, v in filtros.items()])

        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            return response.json()
        elif response.status_code == 401:
            self.autenticar()
            headers = self._get_headers()
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                return response.json()

        raise Exception(f"Erro ao buscar produtos: {response.status_code} - {response.text}")

    def post_produtos(self, dados_produto):
        headers = self._get_headers()
        url = f"{self.base_url}/produto/Produto"

        response = requests.post(url, json=dados_produto, headers=headers)

        if response.status_code in [200, 201]:
            return response.json()
        elif response.status_code == 401:
            self.autenticar()
            headers = self._get_headers()
            response = requests.post(url, json=dados_produto, headers=headers)
            if response.status_code in [200, 201]:
                return response.json()

        raise Exception(f"Erro ao criar produto: {response.status_code} - {response.text}")


if __name__ == "__main__":
    client = APIClient()

    try:
        print("Autenticando...")
        token = client.autenticar()
        if token:
            print(f"Token obtido com sucesso: {token[:50] if len(token) > 50 else token}...")

        print("\nBuscando produtos...")
        produtos = client.get_produtos()
        print(f"Total de produtos encontrados: {len(produtos) if isinstance(produtos, list) else 'N/A'}")

    except Exception as e:
        print(f"Erro: {str(e)}")