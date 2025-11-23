from flask import Flask, request, jsonify
import requests
import os
from flask_cors import CORS # Importa a biblioteca CORS

# --- Configuração de Variável de Ambiente ---
# A chave é lida de forma segura da variável de ambiente no Render.
YOUR_PUSHPAY_API_KEY = os.environ.get("PUSHPAY_API_KEY") 

# --- Configuração do Flask ---
app = Flask(__name__)
CORS(app) # Habilita o CORS para permitir requisições de outras origens (seu index.html local)

# --- Rota da API ---
@app.route('/gerar-pix', methods=['POST'])
def gerar_pix():
    # 1. Verifica se a chave de API foi carregada
    if not YOUR_PUSHPAY_API_KEY:
        print("ERRO: Chave PUSHPAY_API_KEY não carregada.")
        return jsonify({"message": "Erro de configuração: Chave de API não encontrada no servidor."}), 500

    try:
        # 2. Obtém o valor em Reais (R$) do JSON do Front-end (campo 'value')
        data = request.get_json()
        valor_em_reais = data.get('value')

        if not valor_em_reais or not isinstance(valor_em_reais, (int, float)) or valor_em_reais <= 0.50:
            return jsonify({"message": "Valor para PIX inválido ou abaixo do mínimo permitido."}), 400

        # 3. Prepara o payload para a API da PushinPay
        # O campo 'value' deve ser enviado em R$ (float/string), conforme a documentação do curl.
        payload = {
            "value": valor_em_reais,
            "webhook_url": "https://seu-site.com/webhook", # Sugestão: adicione sua URL de webhook
            "split_rules": [],
            "description": "Pagamento de Assinatura Streaming"
        }

        # 4. Envia a requisição para a PushinPay
        headers = {
            "Authorization": f"Bearer {YOUR_PUSHPAY_API_KEY}", 
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        # ⚠️ URL CORRIGIDA: Usa o domínio BR e o endpoint correto /api/pix/cashIn
        pushpay_api_url = "https://api.pushinpay.com.br/api/pix/cashIn" 
        
        # ⚠️ verify=False corrige o erro de certificado SSL no Render
        response = requests.post(pushpay_api_url, headers=headers, json=payload, verify=False)
        
        # 5. Captura erros da API PushinPay (ex: 404, 401, 400)
        response.raise_for_status() 

        pushpay_data = response.json()
        
        # 6. Extrai os dados e retorna ao Front-end (ajustar nomes dos campos conforme a PushinPay)
        # Assumindo que os nomes dos campos para retorno continuam os mesmos da primeira versão (qrcode_url e pix_code)
        pix_code = pushpay_data.get('pix_code')
        qrcode_url = pushpay_data.get('qrcode_url')

        if not pix_code or not qrcode_url:
             return jsonify({
                "message": "Resposta da PushinPay incompleta. Dados PIX (QR Code ou Código) faltando.",
                "details": pushpay_data
            }), 500

        return jsonify({
            "qrcode_url": qrcode_url,
            "pix_code": pix_code,
            "message": "PIX gerado com sucesso."
        })

    except requests.exceptions.HTTPError as err:
        # Este bloco lida com erros da PushinPay (ex: 401 Unauthorized, 404 Not Found)
        error_status = err.response.status_code
        error_text = err.response.text
        
        print(f"ERRO API PUSHPAY: Status {error_status}, Resposta: {error_text}")
        
        return jsonify({
            "message": f"Falha na API da PushinPay (Erro {error_status}). Verifique a chave de API e o valor enviado.",
            "details": error_text
        }), error_status
        
    except Exception as e:
        # Este bloco captura qualquer outro erro interno (500)
        print(f"ERRO INTERNO GRAVE: {str(e)}")
        return jsonify({"message": "Erro interno do servidor ao processar a requisição.", "details": str(e)}), 500

# --- Ponto de Entrada Principal ---
if __name__ == '__main__':
    # Esta parte só roda localmente
    app.run(debug=True)