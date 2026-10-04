import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import requests
import threading
import json
import re
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import os

class APIScannerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("API Scanner - Buscar Credenciais")
        self.root.geometry("1400x900")
        self.root.configure(bg="#1e1e1e")
        
        # Variáveis
        self.scanning = False
        self.found_apis = []
        self.found_credentials = []
        self.found_endpoints = []
        self.har_data = None
        self.har_endpoints_full = []  # Endpoints completos do HAR
        
        # Endpoints conhecidos da API Dabradata
        self.dabradata_endpoints = [
            {"name": "cadastro-pf-plus", "method": "POST", "params": ["cpf", "nome", "data_nascimento"]},
            {"name": "cadastro-pf-basica", "method": "POST", "params": ["cpf"]},
            {"name": "cadastro-pj-plus", "method": "POST", "params": ["cnpj", "razao_social"]},
            {"name": "cadastro-pj-basica", "method": "POST", "params": ["cnpj"]},
            {"name": "consulta-veicular", "method": "POST", "params": ["placa", "renavam"]},
            {"name": "gravame-veicular", "method": "POST", "params": ["placa"]},
            {"name": "habilitacao-cnh", "method": "POST", "params": ["cpf"]},
            {"name": "fipe-veiculo", "method": "POST", "params": ["placa"]},
            {"name": "boa-vista-acerta-pf", "method": "POST", "params": ["cpf"]},
            {"name": "credito-scr-resumo", "method": "POST", "params": ["cpf", "cnpj"]},
            {"name": "protestos-brasil", "method": "POST", "params": ["cpf", "cnpj"]},
            {"name": "ceis-sancoes", "method": "POST", "params": ["cpf", "cnpj"]},
            {"name": "cnep-sancoes", "method": "POST", "params": ["cpf", "cnpj"]},
            {"name": "receita-federal-pf", "method": "POST", "params": ["cpf"]},
            {"name": "receita-federal-pj", "method": "POST", "params": ["cnpj"]},
        ]
        
        # Configurar estilo dark
        self.setup_styles()
        
        # Criar GUI
        self.create_widgets()
        
    def setup_styles(self):
        """Configurar tema dark"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Cores dark theme
        bg_primary = "#1e1e1e"
        bg_secondary = "#2d2d2d"
        fg_text = "#e0e0e0"
        fg_accent = "#00ff88"
        
        style.configure("TFrame", background=bg_primary)
        style.configure("TLabel", background=bg_primary, foreground=fg_text)
        style.configure("TButton", background=bg_secondary, foreground=fg_text)
        style.configure("TEntry", fieldbackground=bg_secondary, foreground=fg_text, borderwidth=1)
        style.map("TButton", background=[("active", fg_accent)])
        style.configure("TLabelframe", background=bg_primary, foreground=fg_text)
        style.configure("TLabelframe.Label", background=bg_primary, foreground=fg_accent)
        
    def create_widgets(self):
        """Criar componentes da GUI"""
        # Frame superior
        top_frame = ttk.Frame(self.root)
        top_frame.pack(fill=tk.X, padx=20, pady=20)
        
        ttk.Label(top_frame, text="URL do Domínio:", font=("Arial", 12, "bold")).pack(side=tk.LEFT, padx=5)
        
        self.url_entry = ttk.Entry(top_frame, width=50, font=("Arial", 11))
        self.url_entry.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)
        self.url_entry.insert(0, "https://app.dabradata.com")
        
        self.scan_button = ttk.Button(top_frame, text="🔍 SCANEAR", command=self.start_scan)
        self.scan_button.pack(side=tk.LEFT, padx=5)
        
        self.load_har_button = ttk.Button(top_frame, text="📂 Carregar HAR", command=self.load_har_file)
        self.load_har_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = ttk.Button(top_frame, text="⏹️ PARAR", command=self.stop_scan, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        self.har_status_var = tk.StringVar(value="Nenhum HAR carregado")
        self.har_status_label = ttk.Label(top_frame, textvariable=self.har_status_var, foreground="#ff9800", font=("Arial", 9))
        self.har_status_label.pack(side=tk.LEFT, padx=15)
        
        # Frame com notebooks (abas)
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Aba 1: Log de Scan
        self.log_frame = ttk.Frame(notebook)
        notebook.add(self.log_frame, text="📋 Log de Scan")
        
        self.log_text = scrolledtext.ScrolledText(
            self.log_frame, 
            bg="#2d2d2d", 
            fg="#00ff88",
            font=("Courier New", 10),
            wrap=tk.WORD
        )
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Aba 2: APIs Encontradas
        self.api_frame = ttk.Frame(notebook)
        notebook.add(self.api_frame, text="🔌 APIs Encontradas")
        
        self.api_text = scrolledtext.ScrolledText(
            self.api_frame,
            bg="#2d2d2d",
            fg="#00ff88",
            font=("Courier New", 10),
            wrap=tk.WORD
        )
        self.api_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Aba 3: Credenciais
        self.cred_frame = ttk.Frame(notebook)
        notebook.add(self.cred_frame, text="🔐 Credenciais Encontradas")
        
        cred_button_frame = ttk.Frame(self.cred_frame)
        cred_button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.export_cred_btn = ttk.Button(
            cred_button_frame,
            text="💾 Exportar Credenciais em HTML",
            command=self.export_credentials_html
        )
        self.export_cred_btn.pack(side=tk.LEFT, padx=5)
        
        self.cred_text = scrolledtext.ScrolledText(
            self.cred_frame,
            bg="#2d2d2d",
            fg="#ff6b6b",
            font=("Courier New", 10),
            wrap=tk.WORD
        )
        self.cred_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Aba 4: Headers & Responses
        self.headers_frame = ttk.Frame(notebook)
        notebook.add(self.headers_frame, text="📡 Headers & Responses")
        
        self.headers_text = scrolledtext.ScrolledText(
            self.headers_frame,
            bg="#2d2d2d",
            fg="#87ceeb",
            font=("Courier New", 9),
            wrap=tk.WORD
        )
        self.headers_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Aba 5: Query Builder
        self.query_frame = ttk.Frame(notebook)
        notebook.add(self.query_frame, text="🔧 Query Builder")
        self.query_frame.grid_columnconfigure(0, weight=1)
        self.query_frame.grid_rowconfigure(1, weight=1)
        
        # Seletor de endpoint com abas
        selector_frame = ttk.LabelFrame(self.query_frame, text="Selecione um Endpoint")
        selector_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Sub-notebook para endpoints
        self.endpoint_notebook = ttk.Notebook(selector_frame)
        self.endpoint_notebook.pack(fill=tk.X, padx=5, pady=5)
        
        # Aba: Padrão (Dabradata)
        padrao_frame = ttk.Frame(self.endpoint_notebook)
        self.endpoint_notebook.add(padrao_frame, text="Dabradata (Padrão)")
        
        ttk.Label(padrao_frame, text="Endpoint:", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=5, pady=5)
        
        self.endpoint_var = tk.StringVar()
        endpoint_list = [ep["name"] for ep in self.dabradata_endpoints]
        self.endpoint_combo = ttk.Combobox(
            padrao_frame,
            textvariable=self.endpoint_var,
            values=endpoint_list,
            state="readonly",
            width=40,
            font=("Arial", 10)
        )
        self.endpoint_combo.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.X, expand=True)
        self.endpoint_combo.bind("<<ComboboxSelected>>", self.on_endpoint_selected)
        
        # Aba: Do HAR
        har_frame = ttk.Frame(self.endpoint_notebook)
        self.endpoint_notebook.add(har_frame, text="Do HAR Carregado")
        
        ttk.Label(har_frame, text="APIs Encontradas:", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=5, pady=5)
        
        self.har_endpoint_var = tk.StringVar()
        self.har_endpoint_combo = ttk.Combobox(
            har_frame,
            textvariable=self.har_endpoint_var,
            values=[],
            state="readonly",
            width=50,
            font=("Arial", 10)
        )
        self.har_endpoint_combo.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.X, expand=True)
        self.har_endpoint_combo.bind("<<ComboboxSelected>>", self.on_har_endpoint_selected)
        
        # Frame para parâmetros
        self.params_frame = ttk.LabelFrame(self.query_frame, text="Parâmetros da Query")
        self.params_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.params_frame.grid_columnconfigure(1, weight=1)
        
        # Container scrollable para parâmetros dinâmicos
        self.params_container = ttk.Frame(self.params_frame)
        self.params_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Token para query builder
        token_frame = ttk.LabelFrame(self.query_frame, text="Autenticação")
        token_frame.pack(fill=tk.X, padx=10, pady=10)
        token_frame.grid_columnconfigure(1, weight=1)
        
        ttk.Label(token_frame, text="Token (Bearer):", font=("Arial", 10)).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        self.query_token_entry = ttk.Entry(token_frame, width=60, font=("Arial", 9))
        self.query_token_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        self.show_token_btn = ttk.Button(
            token_frame,
            text="👁️ Mostrar",
            command=self.toggle_show_token,
            width=10
        )
        self.show_token_btn.grid(row=0, column=2, padx=5, pady=5)
        
        self.copy_token_btn = ttk.Button(
            token_frame,
            text="📋 Copiar",
            command=self.copy_token,
            width=10
        )
        self.copy_token_btn.grid(row=0, column=3, padx=5, pady=5)
        
        self.token_show = False  # Flag para saber se está mostrando o token
        
        # Botões de ação
        action_frame = ttk.Frame(self.query_frame)
        action_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.send_query_btn = ttk.Button(
            action_frame,
            text="📤 Enviar Query",
            command=self.send_query
        )
        self.send_query_btn.pack(side=tk.LEFT, padx=5)
        
        self.copy_curl_btn = ttk.Button(
            action_frame,
            text="📋 Copiar CURL",
            command=self.copy_curl_to_clipboard
        )
        self.copy_curl_btn.pack(side=tk.LEFT, padx=5)
        
        self.export_query_btn = ttk.Button(
            action_frame,
            text="💾 Exportar Query em HTML",
            command=self.export_query_html
        )
        self.export_query_btn.pack(side=tk.LEFT, padx=5)
        
        # Response da query
        response_frame = ttk.LabelFrame(self.query_frame, text="Response")
        response_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.query_response_text = scrolledtext.ScrolledText(
            response_frame,
            bg="#2d2d2d",
            fg="#4ade80",
            font=("Courier New", 9),
            wrap=tk.WORD
        )
        self.query_response_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Aba 6: HAR Data
        self.har_frame = ttk.Frame(notebook)
        notebook.add(self.har_frame, text="📦 HAR Carregado")
        self.har_frame.grid_columnconfigure(0, weight=1)
        self.har_frame.grid_rowconfigure(0, weight=1)
        
        har_button_frame = ttk.Frame(self.har_frame)
        har_button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.export_har_btn = ttk.Button(
            har_button_frame,
            text="💾 Exportar HAR em HTML",
            command=self.export_har_html
        )
        self.export_har_btn.pack(side=tk.LEFT, padx=5)
        
        self.har_text = scrolledtext.ScrolledText(
            self.har_frame,
            bg="#2d2d2d",
            fg="#b0c4de",
            font=("Courier New", 9),
            wrap=tk.WORD
        )
        self.har_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Status bar
        self.status_var = tk.StringVar(value="Pronto para scanear...")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.pack(fill=tk.X, padx=20, pady=10)
        
    def toggle_show_token(self):
        """Alternar entre mostrar e ocultar o token"""
        current = self.query_token_entry.cget('show')
        if current == '*':
            self.query_token_entry.config(show='')
            self.show_token_btn.config(text="👁️‍🗨️ Ocultar")
        else:
            self.query_token_entry.config(show='*')
            self.show_token_btn.config(text="👁️ Mostrar")
    
    def copy_token(self):
        """Copiar token para clipboard"""
        token = self.query_token_entry.get()
        if token:
            self.root.clipboard_clear()
            self.root.clipboard_append(token)
            messagebox.showinfo("Sucesso", "Token copiado para o clipboard!")
        else:
            messagebox.showwarning("Aviso", "Nenhum token para copiar!")
        
    def load_har_file(self):
        """Carregar arquivo HAR"""
        file_path = filedialog.askopenfilename(
            title="Selecione um arquivo HAR",
            filetypes=[("HAR files", "*.har"), ("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if not file_path:
            return
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                self.har_data = json.load(f)
            
            # Extrair informações do HAR
            self.process_har_data()
            
            self.har_status_var.set(f"✓ HAR carregado: {os.path.basename(file_path)}")
            messagebox.showinfo("Sucesso", f"HAR carregado com sucesso!\nEndpoints e credenciais extraídos.")
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar HAR:\n{str(e)}")
            self.har_data = None
    
    def process_har_data(self):
        """Processar dados do arquivo HAR"""
        if not self.har_data:
            return
        
        self.har_text.delete(1.0, tk.END)
        self.found_endpoints = []
        self.found_credentials = []
        self.har_endpoints_full = []
        
        entries = self.har_data.get("log", {}).get("entries", [])
        
        self.har_text.insert(tk.END, f"[*] Total de requisições: {len(entries)}\n\n")
        
        for idx, entry in enumerate(entries, 1):
            request = entry.get("request", {})
            response = entry.get("response", {})
            
            method = request.get("method", "GET")
            url = request.get("url", "")
            headers = request.get("headers", [])
            
            # Armazenar URL completa para query builder
            self.har_endpoints_full.append({
                "url": url,
                "method": method,
                "headers": headers,
                "body": request.get("postData", {})
            })
            
            self.har_text.insert(tk.END, f"[{idx}] {method} {url}\n")
            
            # Extrair tokens dos headers
            for header in headers:
                if isinstance(header, dict):
                    name = header.get("name", "").lower()
                    value = header.get("value", "")
                    
                    if any(token_key in name for token_key in ["authorization", "token", "api-key", "bearer"]):
                        self.har_text.insert(tk.END, f"    🔐 {name}: {value}\n")  # Mostrar token completo
                        self.found_credentials.append({
                            "type": name.upper(),
                            "value": value,
                            "source": url
                        })
                    
                    self.har_text.insert(tk.END, f"    📝 {name}: {value}\n")
            
            # Extrair parâmetros do body
            post_data = request.get("postData", {})
            if post_data:
                text = post_data.get("text", "")
                if text:
                    self.har_text.insert(tk.END, f"    📦 Body: {text[:100]}...\n")
            
            # URL para encontrar endpoint base
            parsed = urlparse(url)
            endpoint = parsed.path
            if endpoint and endpoint not in self.found_endpoints:
                self.found_endpoints.append(endpoint)
            
            self.har_text.insert(tk.END, "\n")
        
        # Atualizar combo de endpoints do HAR
        self.update_har_endpoints_combo()
        
        # Atualizar abas com dados extraídos
        self.display_har_results()
    
    def update_har_endpoints_combo(self):
        """Atualizar o combo com os endpoints do HAR"""
        endpoints_list = [ep["url"] for ep in self.har_endpoints_full]
        self.har_endpoint_combo['values'] = endpoints_list
    
    def on_har_endpoint_selected(self, event=None):
        """Quando um endpoint do HAR é selecionado"""
        selected_url = self.har_endpoint_var.get()
        
        # Encontrar o endpoint no histórico
        endpoint_data = next((ep for ep in self.har_endpoints_full if ep["url"] == selected_url), None)
        
        if endpoint_data:
            # Limpar container de parâmetros
            for widget in self.params_container.winfo_children():
                widget.destroy()
            
            # Extrair parâmetros do body
            post_data = endpoint_data.get("body", {})
            body_text = post_data.get("text", "")
            
            self.param_entries = {}
            
            try:
                if body_text:
                    body_json = json.loads(body_text)
                    
                    for i, (key, value) in enumerate(body_json.items()):
                        ttk.Label(
                            self.params_container,
                            text=f"{key.upper()}:",
                            font=("Arial", 10, "bold")
                        ).grid(row=i, column=0, sticky=tk.W, padx=5, pady=5)
                        
                        entry = ttk.Entry(self.params_container, width=50, font=("Arial", 10))
                        entry.insert(0, str(value))  # Preencher com valor anterior
                        entry.grid(row=i, column=1, sticky=tk.EW, padx=5, pady=5)
                        self.param_entries[key] = entry
                    
                    # Preencher token automaticamente se encontrado
                    headers = endpoint_data.get("headers", [])
                    for header in headers:
                        if isinstance(header, dict):
                            name = header.get("name", "").lower()
                            value = header.get("value", "")
                            
                            if "authorization" in name or "bearer" in name:
                                # Remover "Bearer " se existir
                                token = value.replace("Bearer ", "").replace("bearer ", "")
                                self.query_token_entry.delete(0, tk.END)
                                self.query_token_entry.insert(0, token)
                
            except json.JSONDecodeError:
                ttk.Label(
                    self.params_container,
                    text="Não foi possível parsejar o body como JSON",
                    font=("Arial", 10)
                ).pack(padx=5, pady=10)
            
            self.params_container.grid_columnconfigure(1, weight=1)
    
    def export_credentials_html(self):
        """Exportar credenciais em HTML"""
        if not self.found_credentials:
            messagebox.showwarning("Aviso", "Nenhuma credencial para exportar!")
            return
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".html",
            initialfile="credenciais.html",
            filetypes=[("HTML files", "*.html"), ("All files", "*.*")]
        )
        
        if not file_path:
            return
        
        html_content = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Credenciais Encontradas</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #1e1e1e;
            color: #e0e0e0;
            padding: 20px;
            margin: 0;
        }
        h1 {
            color: #ff9800;
            text-align: center;
            margin-bottom: 30px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            background-color: #2d2d2d;
            border: 2px solid #444;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        }
        thead {
            background-color: #0d47a1;
            color: #fff;
            font-weight: bold;
        }
        th {
            padding: 15px;
            text-align: left;
            border-bottom: 2px solid #444;
        }
        td {
            padding: 12px 15px;
            border-bottom: 1px solid #444;
        }
        tr:hover {
            background-color: #3d3d3d;
        }
        .tipo {
            color: #4ade80;
            font-weight: bold;
        }
        .token {
            color: #ff6b6b;
            font-family: 'Courier New', monospace;
            word-break: break-all;
            max-width: 500px;
        }
        .source {
            color: #87ceeb;
            font-size: 0.9em;
        }
        .footer {
            text-align: center;
            margin-top: 30px;
            color: #999;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔐 Credenciais Encontradas</h1>
        <table>
            <thead>
                <tr>
                    <th>Tipo</th>
                    <th>Token / Valor</th>
                    <th>Source</th>
                </tr>
            </thead>
            <tbody>
"""
        
        for cred in self.found_credentials:
            tipo = cred.get('type', 'Unknown')
            valor = cred.get('value', 'N/A')
            source = cred.get('source', 'N/A')
            
            html_content += f"""
                <tr>
                    <td class="tipo">{tipo}</td>
                    <td class="token">{valor}</td>
                    <td class="source">{source}</td>
                </tr>
"""
        
        html_content += """
            </tbody>
        </table>
        <div class="footer">
            <p>Gerado automaticamente pelo API Scanner</p>
        </div>
    </div>
</body>
</html>
"""
        
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(html_content)
            messagebox.showinfo("Sucesso", f"Credenciais exportadas em HTML:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao exportar HTML:\n{str(e)}")
    
    def export_har_html(self):
        """Exportar dados do HAR em HTML"""
        if not self.har_endpoints_full:
            messagebox.showwarning("Aviso", "Nenhum HAR carregado para exportar!")
            return
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".html",
            initialfile="har_endpoints.html",
            filetypes=[("HTML files", "*.html"), ("All files", "*.*")]
        )
        
        if not file_path:
            return
        
        html_content = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Endpoints do HAR</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #1e1e1e;
            color: #e0e0e0;
            padding: 20px;
            margin: 0;
        }
        h1 {
            color: #ff9800;
            text-align: center;
            margin-bottom: 30px;
        }
        h2 {
            color: #4ade80;
            margin-top: 30px;
            border-bottom: 2px solid #444;
            padding-bottom: 10px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        .endpoint-card {
            background-color: #2d2d2d;
            border: 2px solid #444;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        }
        .method {
            display: inline-block;
            padding: 5px 10px;
            border-radius: 4px;
            font-weight: bold;
            margin-right: 10px;
            color: white;
        }
        .method.post {
            background-color: #2196F3;
        }
        .method.get {
            background-color: #4CAF50;
        }
        .url {
            color: #87ceeb;
            font-family: 'Courier New', monospace;
            word-break: break-all;
            margin: 10px 0;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            background-color: #1b1b1b;
            margin: 10px 0;
        }
        th, td {
            padding: 10px;
            text-align: left;
            border-bottom: 1px solid #444;
        }
        th {
            background-color: #0d47a1;
            color: #fff;
            font-weight: bold;
        }
        .header-name {
            color: #ffeb3b;
        }
        .header-value {
            color: #4ade80;
            font-family: 'Courier New', monospace;
            word-break: break-all;
        }
        .footer {
            text-align: center;
            margin-top: 30px;
            color: #999;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📦 Endpoints Encontrados no HAR</h1>
        <h2>Total de Requisições: """ + str(len(self.har_endpoints_full)) + """</h2>
"""
        
        for idx, ep in enumerate(self.har_endpoints_full, 1):
            method = ep.get('method', 'GET').upper()
            url = ep.get('url', '')
            headers = ep.get('headers', [])
            
            method_class = 'post' if method == 'POST' else 'get'
            
            html_content += f"""
        <div class="endpoint-card">
            <h3>[{idx}] Requisição</h3>
            <div>
                <span class="method {method_class}">{method}</span>
                <span class="url">{url}</span>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>Header</th>
                        <th>Valor</th>
                    </tr>
                </thead>
                <tbody>
"""
            
            for header in headers:
                if isinstance(header, dict):
                    name = header.get('name', '')
                    value = header.get('value', '')
                    html_content += f"""
                    <tr>
                        <td class="header-name">{name}</td>
                        <td class="header-value">{value}</td>
                    </tr>
"""
            
            html_content += """
                </tbody>
            </table>
        </div>
"""
        
        html_content += """
        <div class="footer">
            <p>Gerado automaticamente pelo API Scanner</p>
        </div>
    </div>
</body>
</html>
"""
        
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(html_content)
            messagebox.showinfo("Sucesso", f"HAR exportado em HTML:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao exportar HTML:\n{str(e)}")
    
    def export_query_html(self):
        """Exportar query atual em HTML"""
        endpoint = self.endpoint_var.get()
        har_endpoint = self.har_endpoint_var.get()
        token = self.query_token_entry.get()
        params = self.build_query_json()
        
        if not endpoint and not har_endpoint:
            messagebox.showwarning("Aviso", "Selecione um endpoint primeiro!")
            return
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".html",
            initialfile="query.html",
            filetypes=[("HTML files", "*.html"), ("All files", "*.*")]
        )
        
        if not file_path:
            return
        
        if har_endpoint:
            url = har_endpoint
        else:
            url = f"https://app.dabradata.com/api/v1/consulta/{endpoint}"
        
        curl = self.build_curl_command()
        
        html_content = f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Query API</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #1e1e1e;
            color: #e0e0e0;
            padding: 20px;
            margin: 0;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        h1 {{
            color: #ff9800;
            text-align: center;
        }}
        .section {{
            background-color: #2d2d2d;
            border: 2px solid #444;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        }}
        h2 {{
            color: #4ade80;
            border-bottom: 2px solid #444;
            padding-bottom: 10px;
        }}
        .field {{
            margin: 15px 0;
            padding: 10px;
            background-color: #1b1b1b;
            border-left: 4px solid #0d47a1;
            border-radius: 4px;
        }}
        .field-label {{
            color: #ffeb3b;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        .field-value {{
            color: #87ceeb;
            font-family: 'Courier New', monospace;
            word-break: break-all;
            padding: 10px;
            background-color: #0f1117;
            border-radius: 4px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #444;
        }}
        th {{
            background-color: #0d47a1;
            color: #fff;
            font-weight: bold;
        }}
        .footer {{
            text-align: center;
            margin-top: 30px;
            color: #999;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📤 Query API</h1>
        
        <div class="section">
            <h2>Informações da Requisição</h2>
            <div class="field">
                <div class="field-label">Endpoint:</div>
                <div class="field-value">{url}</div>
            </div>
            <div class="field">
                <div class="field-label">Método:</div>
                <div class="field-value">POST</div>
            </div>
        </div>
        
        <div class="section">
            <h2>Autenticação</h2>
            <div class="field">
                <div class="field-label">Token (Bearer):</div>
                <div class="field-value">{token if token else 'Não definido'}</div>
            </div>
        </div>
        
        <div class="section">
            <h2>Parâmetros</h2>
            <table>
                <thead>
                    <tr>
                        <th>Parâmetro</th>
                        <th>Valor</th>
                    </tr>
                </thead>
                <tbody>
"""
        
        for key, value in params.items():
            html_content += f"""
                    <tr>
                        <td>{key}</td>
                        <td>{value}</td>
                    </tr>
"""
        
        html_content += f"""
                </tbody>
            </table>
        </div>
        
        <div class="section">
            <h2>Comando CURL</h2>
            <div class="field">
                <div class="field-value">{curl}</div>
            </div>
        </div>
        
        <div class="footer">
            <p>Gerado automaticamente pelo API Scanner</p>
        </div>
    </div>
</body>
</html>
"""
        
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(html_content)
            messagebox.showinfo("Sucesso", f"Query exportada em HTML:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao exportar HTML:\n{str(e)}")
    
    def display_har_results(self):
        """Exibir resultados do HAR nas abas"""
        # Endpoints encontrados
        self.api_text.delete(1.0, tk.END)
        if self.found_endpoints:
            self.api_text.insert(tk.END, f"[+] Total de ENDPOINTS encontrados no HAR: {len(self.found_endpoints)}\n\n")
            for endpoint in self.found_endpoints:
                self.api_text.insert(tk.END, f"🔗 {endpoint}\n")
            
            self.api_text.insert(tk.END, f"\n[+] Total de REQUISIÇÕES completas: {len(self.har_endpoints_full)}\n\n")
            for i, ep in enumerate(self.har_endpoints_full, 1):
                self.api_text.insert(tk.END, f"[{i}] {ep['method']} {ep['url']}\n")
        else:
            self.api_text.insert(tk.END, "Nenhum endpoint encontrado no HAR.")
        
        # Credenciais encontradas
        self.cred_text.delete(1.0, tk.END)
        if self.found_credentials:
            self.cred_text.insert(tk.END, f"[!] CREDENCIAIS ENCONTRADAS NO HAR: {len(self.found_credentials)}\n\n")
            for cred in self.found_credentials:
                self.cred_text.insert(tk.END, f"Tipo: {cred.get('type', 'Unknown')}\n")
                self.cred_text.insert(tk.END, f"Valor: {cred.get('value', 'N/A')}\n")
                self.cred_text.insert(tk.END, f"Source: {cred.get('source', 'N/A')}\n")
                self.cred_text.insert(tk.END, f"---\n\n")
        else:
            self.cred_text.insert(tk.END, "Nenhuma credencial encontrada no HAR.")
        
    def on_endpoint_selected(self, event=None):
        """Atualizar campos de parâmetros quando endpoint Dabradata é selecionado"""
        selected = self.endpoint_var.get()
        
        # Limpar container anterior
        for widget in self.params_container.winfo_children():
            widget.destroy()
        
        # Encontrar endpoint selecionado
        endpoint = next((ep for ep in self.dabradata_endpoints if ep["name"] == selected), None)
        
        if endpoint:
            self.param_entries = {}
            
            for i, param in enumerate(endpoint["params"]):
                ttk.Label(self.params_container, text=f"{param.upper()}:", font=("Arial", 10, "bold")).grid(
                    row=i, column=0, sticky=tk.W, padx=5, pady=5
                )
                
                entry = ttk.Entry(self.params_container, width=50, font=("Arial", 10))
                entry.grid(row=i, column=1, sticky=tk.EW, padx=5, pady=5)
                self.param_entries[param] = entry
            
            self.params_container.grid_columnconfigure(1, weight=1)
    
    def build_query_json(self):
        """Construir JSON da query a partir dos parâmetros"""
        query_json = {}
        
        if hasattr(self, 'param_entries'):
            for param, entry in self.param_entries.items():
                value = entry.get().strip()
                if value:
                    query_json[param] = value
        
        return query_json
    
    def build_curl_command(self):
        """Construir comando CURL completo"""
        endpoint = self.endpoint_var.get()
        har_endpoint = self.har_endpoint_var.get()
        
        if not endpoint and not har_endpoint:
            return "Selecione um endpoint primeiro!"
        
        token = self.query_token_entry.get().strip()
        query_json = self.build_query_json()
        
        if har_endpoint:
            # Usar URL completa do HAR
            url = har_endpoint
        else:
            # Usar endpoint padrão
            url = f"https://app.dabradata.com/api/v1/consulta/{endpoint}"
        
        curl_cmd = f'curl -X POST "{url}"'
        
        if token:
            curl_cmd += f' -H "Authorization: Bearer {token}"'
        
        curl_cmd += f' -H "Content-Type: application/json"'
        
        if query_json:
            curl_cmd += f" --data-raw '{json.dumps(query_json)}'"
        else:
            curl_cmd += " --data-raw '{}'"
        
        return curl_cmd
    
    def copy_curl_to_clipboard(self):
        """Copiar comando CURL para clipboard"""
        curl = self.build_curl_command()
        self.root.clipboard_clear()
        self.root.clipboard_append(curl)
        messagebox.showinfo("Sucesso", "CURL copiado para o clipboard!")
    
    def send_query(self):
        """Enviar query para a API"""
        endpoint = self.endpoint_var.get()
        har_endpoint = self.har_endpoint_var.get()
        
        if not endpoint and not har_endpoint:
            messagebox.showerror("Erro", "Selecione um endpoint primeiro!")
            return
        
        token = self.query_token_entry.get().strip()
        if not token:
            messagebox.showerror("Erro", "Insira um token válido!")
            return
        
        query_json = self.build_query_json()
        
        if not query_json:
            messagebox.showerror("Erro", "Preencha pelo menos um parâmetro!")
            return
        
        if har_endpoint:
            url = har_endpoint
        else:
            url = f"https://app.dabradata.com/api/v1/consulta/{endpoint}"
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        self.query_response_text.delete(1.0, tk.END)
        self.query_response_text.insert(tk.END, f"Enviando para {url}...\n\n")
        self.root.update()
        
        try:
            response = requests.post(url, json=query_json, headers=headers, timeout=30, verify=False)
            
            self.query_response_text.insert(tk.END, f"Status: {response.status_code}\n\n")
            
            try:
                response_json = response.json()
                self.query_response_text.insert(tk.END, json.dumps(response_json, ensure_ascii=False, indent=2))
            except:
                self.query_response_text.insert(tk.END, response.text)
                
        except Exception as e:
            self.query_response_text.insert(tk.END, f"Erro: {str(e)}")
        
    def log(self, message, tag="default"):
        """Adicionar mensagem ao log"""
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.root.update()
        
    def start_scan(self):
        """Iniciar scan em thread separada"""
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showerror("Erro", "Insira uma URL válida!")
            return
        
        self.scanning = True
        self.scan_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        
        self.log_text.delete(1.0, tk.END)
        
        self.found_apis = []
        
        thread = threading.Thread(target=self.scan_domain, args=(url,), daemon=True)
        thread.start()
        
    def stop_scan(self):
        """Parar o scan"""
        self.scanning = False
        self.scan_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.status_var.set("Scan cancelado pelo usuário")
        
    def scan_domain(self, url):
        """Executar scan do domínio"""
        try:
            self.status_var.set("Iniciando scan...")
            self.log(f"[*] Iniciando scan de: {url}\n")
            
            # Normalizar URL
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            parsed_url = urlparse(url)
            domain = parsed_url.netloc
            base_url = f"{parsed_url.scheme}://{domain}"
            
            self.log(f"[*] Domínio: {domain}")
            self.log(f"[*] Base URL: {base_url}\n")
            
            # 1. Escanear endpoints comuns
            self.scan_common_endpoints(base_url)
            
            # 2. Verificar documentação de API
            self.check_api_docs(base_url)
            
            self.status_var.set("Scan concluído!")
            self.log(f"\n[✓] Scan finalizado!")
            
        except Exception as e:
            self.log(f"[!] Erro: {str(e)}")
            self.status_var.set(f"Erro: {str(e)}")
        finally:
            self.scan_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            self.scanning = False
            
    def scan_common_endpoints(self, base_url):
        """Scanear endpoints API comuns"""
        if not self.scanning:
            return
            
        self.log("\n[*] Procurando endpoints comuns...")
        
        common_endpoints = [
            "/api",
            "/api/v1",
            "/api/v2",
            "/rest",
            "/graphql",
            "/swagger",
            "/swagger-ui.html",
            "/api-docs",
            "/docs",
        ]
        
        headers = self.get_request_headers()
        
        for endpoint in common_endpoints:
            if not self.scanning:
                break
                
            test_url = urljoin(base_url, endpoint)
            try:
                resp = requests.get(test_url, timeout=5, headers=headers, verify=False)
                if resp.status_code < 400:
                    self.log(f"[+] Encontrado: {test_url} (Status: {resp.status_code})")
                    self.found_apis.append(test_url)
            except:
                pass
                
    def check_api_docs(self, base_url):
        """Procurar documentação de API"""
        if not self.scanning:
            return
            
        self.log("\n[*] Procurando documentação de API...")
        
        doc_patterns = [
            "/swagger-ui.html",
            "/api-docs",
            "/docs",
        ]
        
        headers = self.get_request_headers()
        
        for pattern in doc_patterns:
            if not self.scanning:
                break
                
            url = urljoin(base_url, pattern)
            try:
                resp = requests.get(url, timeout=5, headers=headers, verify=False)
                if resp.status_code == 200:
                    self.log(f"[+] Documentação encontrada: {url}")
            except:
                pass
                
    def get_request_headers(self):
        """Obter headers padrão para requests"""
        return {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json, application/xml, */*",
            "Accept-Language": "en-US,en;q=0.9",
        }

if __name__ == "__main__":
    root = tk.Tk()
    app = APIScannerGUI(root)
    root.mainloop()
