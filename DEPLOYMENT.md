# Guia de Implantação - AL Drones Population Analysis Tool

## 🚀 Opções de Deploy

### 1. Streamlit Cloud (Recomendado para protótipos)

**Vantagens:**
- Gratuito para projetos públicos
- Deploy automático via GitHub
- SSL automático
- Fácil configuração

**Passos:**

1. Faça push do código para o GitHub
2. Acesse [streamlit.io/cloud](https://streamlit.io/cloud)
3. Conecte sua conta GitHub
4. Selecione o repositório
5. Configure:
   - Main file: `app.py`
   - Python version: 3.10
6. Deploy!

**URL resultante:** `https://your-app-name.streamlit.app`

### 2. Heroku

**Vantagens:**
- Maior controle
- Suporte a domínios customizados
- Fácil escalonamento

**Arquivos necessários:**

```bash
# Procfile
web: sh setup.sh && streamlit run app.py

# setup.sh
mkdir -p ~/.streamlit/
echo "\
[server]\n\
headless = true\n\
port = $PORT\n\
enableCORS = false\n\
\n\
" > ~/.streamlit/config.toml

# runtime.txt
python-3.10.12
```

**Deploy:**

```bash
heroku login
heroku create aldrones-population-tool
git push heroku main
heroku open
```

### 3. AWS EC2 (Para produção)

**Vantagens:**
- Controle total
- Alta disponibilidade
- Escalabilidade

**Passos:**

1. **Provisionar EC2:**
   - Ubuntu 22.04 LTS
   - t3.medium ou superior (2 vCPU, 4GB RAM)
   - Security Group: portas 22, 80, 443

2. **Instalar dependências:**
```bash
# Conectar via SSH
ssh -i your-key.pem ubuntu@your-ec2-ip

# Atualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar Python e dependências
sudo apt install python3-pip python3-venv nginx -y
sudo apt install gdal-bin libgdal-dev g++ -y

# Clonar repositório
git clone https://github.com/aldrones/population-analysis-tool.git
cd population-analysis-tool

# Criar ambiente virtual
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

3. **Configurar Nginx:**
```nginx
# /etc/nginx/sites-available/aldrones
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/aldrones /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

4. **Configurar Systemd Service:**
```ini
# /etc/systemd/system/aldrones.service
[Unit]
Description=AL Drones Streamlit App
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/population-analysis-tool
Environment="PATH=/home/ubuntu/population-analysis-tool/venv/bin"
ExecStart=/home/ubuntu/population-analysis-tool/venv/bin/streamlit run app.py

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable aldrones
sudo systemctl start aldrones
sudo systemctl status aldrones
```

5. **SSL com Let's Encrypt:**
```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d your-domain.com
```

### 4. Docker (Portável)

**Deploy local:**
```bash
docker-compose up -d
```

**Deploy em servidor:**
```bash
# Transferir arquivos
scp -r . user@server:/path/to/app/

# No servidor
cd /path/to/app
docker-compose up -d
```

### 5. Google Cloud Run

**Vantagens:**
- Serverless
- Auto-scaling
- Pay-per-use

**Deploy:**
```bash
# Instalar gcloud CLI
gcloud init

# Build e deploy
gcloud builds submit --tag gcr.io/PROJECT_ID/aldrones-app
gcloud run deploy aldrones-app \
  --image gcr.io/PROJECT_ID/aldrones-app \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

## 🔒 Segurança

### Variáveis de Ambiente

Crie arquivo `.env`:
```bash
# Streamlit
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0

# IBGE API (se necessário)
IBGE_API_TIMEOUT=60

# Application
MAX_UPLOAD_SIZE_MB=200
```

### Autenticação (Opcional)

Para adicionar autenticação básica ao Streamlit:

```python
# auth.py
import streamlit as st
import hmac

def check_password():
    """Returns True if password is correct."""
    
    def password_entered():
        if hmac.compare_digest(st.session_state["password"], st.secrets["password"]):
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if st.session_state.get("password_correct", False):
        return True

    st.text_input(
        "Password", type="password", on_change=password_entered, key="password"
    )
    if "password_correct" in st.session_state:
        st.error("😕 Password incorrect")
    return False

# No app.py
from auth import check_password

if not check_password():
    st.stop()
```

Adicionar em `.streamlit/secrets.toml`:
```toml
password = "sua-senha-segura"
```

## 📊 Monitoramento

### Logs

**Streamlit Cloud:**
- Acessível via dashboard

**Servidor próprio:**
```bash
# Systemd logs
sudo journalctl -u aldrones -f

# Application logs
tail -f logs/app.log
```

### Métricas

Adicionar ao `app.py`:
```python
import time
import logging

# Configure logging
logging.basicConfig(
    filename='logs/app.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Track usage
def log_usage(action):
    logging.info(f"Action: {action} | Time: {time.time()}")
```

## 🔄 Backup

### Dados IBGE
Os dados do IBGE são baixados sob demanda e armazenados em `dados_ibge/`. 
Para backup:

```bash
# Criar backup
tar -czf ibge_data_backup.tar.gz dados_ibge/

# Restaurar backup
tar -xzf ibge_data_backup.tar.gz
```

## 📈 Performance

### Otimizações:

1. **Cache de grids IBGE:**
   - Já implementado no código
   - Mantém grids em memória durante sessão

2. **Limitar concurrent users:**
   - Streamlit Cloud: 1 concurrent user (free tier)
   - Servidor próprio: ajustar via Nginx

3. **CDN para assets estáticos:**
   - Considerar CloudFlare para logo e CSS

## 🆘 Troubleshooting

### Erro: "GDAL not found"
```bash
sudo apt install gdal-bin libgdal-dev
pip install gdal==$(gdal-config --version)
```

### Erro: "Memory error"
- Aumentar RAM do servidor
- Limitar área de análise
- Implementar processamento em chunks

### Erro: "Connection timeout IBGE"
- Verificar conectividade
- Aumentar timeout no código
- Considerar mirror dos dados IBGE

## 📞 Suporte

Para questões técnicas:
- Email: contato@aldrones.com.br
- GitHub Issues: [github.com/aldrones/population-analysis-tool/issues](https://github.com/aldrones/population-analysis-tool/issues)
