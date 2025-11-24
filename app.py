from flask import Flask, request, jsonify
import requests
import os
from flask_cors import CORS 
from decimal import Decimal, ROUND_HALF_UP

# --- Configuração de Variável de Ambiente ---
# Assume que a chave de Produção (LIVE) está configurada no Render
YOUR_PUSHPAY_API_KEY = os.environ.get("PUSHPAY_API_KEY") 

# --- Configuração do Flask ---
app = Flask(__name__)
# Permite que seu index.html local (ou em outro domínio) chame esta API
CORS(app) 

# URL FINALMENTE ATUALIZADA PARA PRODUÇÃO (LIVE)
PUSHINPAY_BASE_URL = "https://api.pushinpay.com.br/api" 

# --- ROTA DE RAIZ (NOVA) ---
@app.route('/')
def home():
    """
    Rota de diagnóstico para a URL base. Confirma que o servidor está ativo.
    """
    return """
    <h1>API do PIX Rodando! ✅</h1>
    <p>Esta é a API (Back-end) para geração de PIX da PushinPay.</p>
    <p>Para usar: Abra seu arquivo <b>index.html</b> e clique em 'Pagar com PIX Agora'.</p>
    <p>Endpoint de pagamento: /gerar-pix (método POST)</p>
    """, 200

# --- ROTA PRINCIPAL DE GERAÇÃO DO PIX ---
@app.route('/gerar-pix', methods=['POST'])
def gerar_pix():
    if not YOUR_PUSHPAY_API_KEY:
        print("ERRO: Chave PUSHPAY_API_KEY não carregada.")
        return jsonify({"message": "Erro de configuração: Chave de API não encontrada no servidor."}), 500

    try:
        data = request.get_json()
        # Recebe o 'value' em Reais (ex: 49.90) do Front-end
        valor_em_reais = data.get('value')

        if not valor_em_reais or not isinstance(valor_em_reais, (int, float)) or valor_em_reais <= 0.50:
            return jsonify({"message": "Valor para PIX inválido ou abaixo do mínimo permitido (R$ 0,50)."}), 400

        # CONVERSÃO PARA CENTAVOS (R$ 49.90 -> 4990)
        valor_decimal = Decimal(str(valor_em_reais))
        valor_em_centavos = int(valor_decimal.quantize(Decimal('0.00'), rounding=ROUND_HALF_UP) * 100)
        
        payload = {
            "value": valor_em_centavos, 
            "webhook_url": "https://seu-site.com/webhook", 
            "split_rules": [],
            "description": "Pagamento de Assinatura Streaming"
        }

        headers = {
            "Authorization": f"Bearer {YOUR_PUSHPAY_API_KEY}", 
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        pushpay_api_url = f"{PUSHINPAY_BASE_URL}/pix/cashIn" 
        
        # O verify=False corrige problemas de certificado SSL no ambiente do Render/Python
        response = requests.post(pushpay_api_url, headers=headers, json=payload, verify=False)
        
        # Lança um erro se o status for 4xx (como 401, 422) ou 5xx
        response.raise_for_status() 

        pushpay_data = response.json()
        
        # 🟢 CORREÇÃO DE EXIBIÇÃO: Mapeamento dos campos corretos
        # Estes são os campos que o seu Front-end espera
        pix_code = pushpay_data.get('qr_code')        # Código Copia e Cola (TEXTO)
        qrcode_url = pushpay_data.get('qr_code_base64') # Imagem QR Code (Base64)

        if not pix_code or not qrcode_url:
             return jsonify({
                "message": "Resposta da PushinPay incompleta. Dados PIX faltando.",
                "details": pushpay_data
            }), 500

        # Envia os dados de sucesso para o Front-end
        return jsonify({
            "qrcode_url": qrcode_url, 
            "pix_code": pix_code,
            "message": "PIX gerado com sucesso."
        })

    except requests.exceptions.HTTPError as err:
        error_status = err.response.status_code
        error_text = err.response.text
        
        print(f"ERRO API PUSHPAY: Status {error_status}, Resposta: {error_text}")
        
        # Retorna o erro capturado para o Front-end tratar
        return jsonify({
            "message": f"Falha na API da PushinPay (Erro {error_status}).",
            "details": error_text
        }), error_status
        
    except Exception as e:
        print(f"ERRO INTERNO GRAVE: {str(e)}")
        return jsonify({"message": "Erro interno do servidor ao processar a requisição.", "details": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    # O host '0.0.0.0' é obrigatório para o Render funcionar corretamente
    app.run(host='0.0.0.0', port=port)