import customtkinter as ctk
from tkinter import ttk, messagebox, scrolledtext
import requests
import json

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")


class APITesterApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Dabradata API Tester")
        self.geometry("1400x900")
        self.minsize(1200, 800)

        self.token = ""
        self.last_response = None

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Header
        self.header = ctk.CTkLabel(
            self,
            text="Dabradata API Tester",
            font=("Segoe UI", 26, "bold"),
        )
        self.header.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")

        # Main frame
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=1)

        # Top control panel
        self.control_panel = ctk.CTkFrame(self.main_frame)
        self.control_panel.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        self.control_panel.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(self.control_panel, text="Token:", font=("Segoe UI", 11)).pack(side="left", padx=(0, 10))

        self.token_entry = ctk.CTkEntry(
            self.control_panel,
            placeholder_text="Cole seu token aqui...",
            width=400,
            height=36
        )
        self.token_entry.pack(side="left", fill="x", expand=True, padx=(0, 20))

        self.save_token_btn = ctk.CTkButton(
            self.control_panel,
            text="Salvar Token",
            command=self.save_token,
            width=120,
            height=36
        )
        self.save_token_btn.pack(side="left", padx=(0, 10))

        self.token_status = ctk.CTkLabel(
            self.control_panel,
            text="Token não definido",
            text_color="#FF6B6B",
            font=("Segoe UI", 10)
        )
        self.token_status.pack(side="left", padx=10)

        # Content with two columns
        self.content_frame = ctk.CTkFrame(self.main_frame)
        self.content_frame.grid(row=1, column=0, sticky="nsew")
        self.content_frame.grid_columnconfigure(0, weight=0)
        self.content_frame.grid_columnconfigure(1, weight=1)
        self.content_frame.grid_rowconfigure(0, weight=1)

        # Left panel - API List
        self.left_panel = ctk.CTkFrame(self.content_frame, fg_color="#1b1d22", corner_radius=10)
        self.left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        self.left_panel.grid_columnconfigure(0, weight=1)
        self.left_panel.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(self.left_panel, text="APIs Disponíveis", font=("Segoe UI", 14, "bold")).grid(row=0, column=0, padx=10, pady=10, sticky="w")

        self.api_listbox = ctk.CTkTextbox(
            self.left_panel,
            width=300,
            fg_color="#0f1117",
            text_color="#f0f5ff",
            border_color="#2d323c",
            corner_radius=8
        )
        self.api_listbox.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")
        self.api_listbox.configure(state="disabled")

        # Right panel - Notebook (tabbed interface)
        self.right_panel = ctk.CTkFrame(self.content_frame)
        self.right_panel.grid(row=0, column=1, sticky="nsew")
        self.right_panel.grid_columnconfigure(0, weight=1)
        self.right_panel.grid_rowconfigure(0, weight=1)

        self.notebook = ttk.Notebook(self.right_panel)
        self.notebook.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)

        # Tab 1: Request Builder
        self.tab_request = ctk.CTkFrame(self.notebook)
        self.notebook.add(self.tab_request, text="Request Builder")
        self.tab_request.grid_columnconfigure(0, weight=1)
        self.tab_request.grid_rowconfigure(2, weight=1)

        # Request builder content
        self.setup_request_tab()

        # Tab 2: Response
        self.tab_response = ctk.CTkFrame(self.notebook)
        self.notebook.add(self.tab_response, text="Response")
        self.tab_response.grid_columnconfigure(0, weight=1)
        self.tab_response.grid_rowconfigure(0, weight=1)

        self.response_text = ctk.CTkTextbox(
            self.tab_response,
            fg_color="#0f1117",
            text_color="#4ade80",
            border_color="#2d323c",
            corner_radius=8
        )
        self.response_text.pack(fill="both", expand=True, padx=10, pady=10)

        # Tab 3: History
        self.tab_history = ctk.CTkFrame(self.notebook)
        self.notebook.add(self.tab_history, text="Histórico")
        self.tab_history.grid_columnconfigure(0, weight=1)
        self.tab_history.grid_rowconfigure(0, weight=1)

        self.history_text = ctk.CTkTextbox(
            self.tab_history,
            fg_color="#0f1117",
            text_color="#f0f5ff",
            border_color="#2d323c",
            corner_radius=8
        )
        self.history_text.pack(fill="both", expand=True, padx=10, pady=10)

        self.load_apis()

    def setup_request_tab(self):
        # Endpoint selection
        endpoint_frame = ctk.CTkFrame(self.tab_request)
        endpoint_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(endpoint_frame, text="Endpoint:", font=("Segoe UI", 11, "bold")).pack(side="left", padx=(0, 10))
        
        self.endpoint_var = ctk.StringVar()
        self.endpoint_combo = ctk.CTkComboBox(
            endpoint_frame,
            variable=self.endpoint_var,
            values=self.get_api_endpoints(),
            state="readonly",
            width=400,
            height=36
        )
        self.endpoint_combo.pack(side="left", fill="x", expand=True)

        # Query Parameters
        param_frame = ctk.CTkFrame(self.tab_request)
        param_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        param_frame.grid_columnconfigure(0, weight=1)
        param_frame.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(param_frame, text="Parâmetros JSON (Body):", font=("Segoe UI", 11, "bold")).grid(row=0, column=0, sticky="w", pady=(0, 5))

        self.param_text = ctk.CTkTextbox(
            param_frame,
            height=15,
            fg_color="#0f1117",
            text_color="#f0f5ff",
            border_color="#2d323c",
            corner_radius=8
        )
        self.param_text.grid(row=1, column=0, sticky="nsew")
        self.param_text.insert("1.0", "{}")

        # Action buttons
        button_frame = ctk.CTkFrame(self.tab_request)
        button_frame.pack(fill="x", padx=10, pady=(0, 10))

        self.send_btn = ctk.CTkButton(
            button_frame,
            text="Enviar Requisição",
            command=self.send_request,
            width=180,
            height=40,
            fg_color="#2f6fed",
            hover_color="#245bc7",
            font=("Segoe UI", 12, "bold")
        )
        self.send_btn.pack(side="left", padx=(0, 10))

        self.copy_curl_btn = ctk.CTkButton(
            button_frame,
            text="Copiar CURL",
            command=self.copy_curl,
            width=120,
            height=40
        )
        self.copy_curl_btn.pack(side="left", padx=(0, 10))

        self.clear_btn = ctk.CTkButton(
            button_frame,
            text="Limpar",
            command=self.clear_params,
            width=100,
            height=40
        )
        self.clear_btn.pack(side="left")

    def load_apis(self):
        apis = self.get_api_endpoints()
        self.api_listbox.configure(state="normal")
        self.api_listbox.delete("1.0", "end")
        
        categories = {
            "Meio Ambiente": ["ibama-debitos", "ibama-embargo", "ibama-regularidade", "ibama-autuacoes"],
            "Documentação": ["registration-brazil", "registration-mexico", "similarity-mexico", "curp-mexico"],
            "Banco Central": ["bc-inabilitados", "bc-proibidos"],
            "Programas Sociais": ["assistencia-social-pf", "auxilio-emergencial", "bolsa-familia", "bpc-beneficio"],
            "Crédito & Bureau": ["boa-vista-acerta-pf", "credito-scr-resumo", "protestos-brasil", "score-credito-quod"],
            "Compliance": ["ceis-sancoes", "cnep-sancoes", "cepim", "midia-adversa", "pep-exposicao", "aml-vinculos"],
            "Cadastral": ["cadastro-pf-plus", "cadastro-pf-basica", "cadastro-pj-plus", "receita-federal-pf", "receita-federal-pj"],
            "Veículos": ["consulta-veicular", "gravame-veicular", "habilitacao-cnh", "fipe-veiculo"],
            "Processos": ["processos-completa", "processos-agrupada", "tj-processos", "tcu-processo"],
        }

        for category, apis_list in categories.items():
            self.api_listbox.insert("end", f"\n{category}:\n", "category")
            for api in apis_list:
                if api in apis:
                    self.api_listbox.insert("end", f"  • {api}\n")

        self.api_listbox.configure(state="disabled")

    def get_api_endpoints(self):
        return [
            "ibama-debitos", "ibama-embargo", "ibama-regularidade", "ibama-autuacoes",
            "registration-brazil", "registration-mexico", "similarity-mexico", "curp-mexico",
            "bc-inabilitados", "bc-proibidos",
            "assistencia-social-pf", "auxilio-emergencial", "auxilio-reconstrucao", "bpc-beneficio",
            "bolsa-familia", "garantia-safra", "peti-trabalho-infantil", "seguro-defeso",
            "ccd-pf", "ccd-pj",
            "tst-cndt",
            "leads-contato", "enriquecimento-lead", "leads-endereco",
            "acordos-leniencia", "oab-advogados", "cvm-processos-sancionadores", "cvm-valores-mobiliarios",
            "anbima-certificado-edu", "bet-safe-compliance", "cnia-improbidade", "ceis-sancoes", "cnep-sancoes",
            "cepim", "ceaf-expulsoes", "sicaf-fornecedor", "listas-restritivas", "midia-adversa", "offshore-leaks",
            "pep-exposicao", "aml-vinculos",
            "confea-crea", "crbm", "crf",
            "boa-vista-acerta-pf", "boa-vista-risco-pj", "credito-scr-resumo", "credito-scr-analitico",
            "boa-vista-limite-pj", "nuclea-concentracao-transacionado", "nuclea-predicao-transacionado",
            "nuclea-historico-transacionado", "protestos-brasil", "detalhamento-negativo", "boa-vista-completo-pf",
            "score-credito-quod",
            "tse-situacao", "tse-titulo",
            "antt-regularidade", "cadin-sp", "cadin-estadual", "cadin-federal", "cadin-prefeitura-sp",
            "carf-recursos-fiscais", "pgfn-devedores", "nfe-completa", "nfe-inutilizacoes",
            "sintegra-estadual", "suframa-consulta",
            "fincen-crimes", "feriados", "onu-sancoes", "fbi-wanted", "interpol-consulta",
            "eu-sancoes", "uk-sancoes", "ofac-sancoes", "dfat-sancoes-australia",
            "sema-sancoes-canada", "seco-sancoes-suica",
            "antecedentes-federais", "mpmt-investigacao", "cnj-mandados-prisao", "prf-infracoes",
            "processos-completa", "processos-agrupada", "processos-simplificada",
            "sms-enviar", "otp-send", "otp-resend", "sms-status", "otp-verify",
            "cadastro-pf-plus", "cadastro-pf-basica", "cadastro-rf-pf", "dados-cadastrais-basicos",
            "consulta-obito", "nivel-socioeconomico", "cadastro-pj-basica", "cadastro-pj-plus",
            "participacao-societaria", "vinculos-societarios-bases", "relacao-filiais", "vinculos-societarios",
            "vinculos-ubo", "receita-federal-pf", "receita-federal-pj", "receita-federal-pj-live",
            "restituicao-irpf", "simples-nacional",
            "agricultura-familiar-pf", "agricultura-familiar-pj", "apf-rural", "car-ambiental",
            "cafir-imoveis", "dap-pf", "dap-pj",
            "pis-trabalho", "fgts-regularidade", "historico-profissional", "vinculo-empregaticio", "mpt-consulta",
            "tj-processos", "tcu-processo", "tcu-consolidada", "tcu-licitante", "trt-consulta",
            "cep", "consulta-veicular", "gravame-veicular", "habilitacao-cnh", "fipe-veiculo",
        ]

    def save_token(self):
        token = self.token_entry.get()
        if not token.strip():
            messagebox.showwarning("Aviso", "Digite um token válido")
            return
        
        self.token = token
        self.token_status.configure(text="✓ Token definido", text_color="#4ade80")
        messagebox.showinfo("Sucesso", "Token salvo com sucesso!")

    def send_request(self):
        if not self.token:
            messagebox.showwarning("Aviso", "Defina um token antes de enviar")
            return

        endpoint = self.endpoint_var.get()
        if not endpoint:
            messagebox.showwarning("Aviso", "Selecione um endpoint")
            return

        try:
            params_str = self.param_text.get("1.0", "end-1c")
            params = json.loads(params_str) if params_str.strip() else {}
        except json.JSONDecodeError:
            messagebox.showerror("Erro", "JSON inválido nos parâmetros")
            return

        url = f"https://app.dabradata.com/api/v1/consulta/{endpoint}"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}"
        }

        try:
            response = requests.post(url, json=params, headers=headers, timeout=30)
            
            self.last_response = {
                "url": url,
                "method": "POST",
                "headers": headers,
                "body": params,
                "status": response.status_code,
                "response": response.text
            }

            # Display response
            self.response_text.configure(state="normal")
            self.response_text.delete("1.0", "end")
            self.response_text.insert("end", f"Status: {response.status_code}\n\n")
            
            try:
                response_json = response.json()
                self.response_text.insert("end", json.dumps(response_json, ensure_ascii=False, indent=2))
            except:
                self.response_text.insert("end", response.text)
            
            self.response_text.configure(state="disabled")

            # Add to history
            self.history_text.configure(state="normal")
            history_entry = f"\n{'='*60}\n"
            history_entry += f"Timestamp: {json.dumps({'endpoint': endpoint, 'status': response.status_code})}\n"
            history_entry += f"Parâmetros: {json.dumps(params, ensure_ascii=False)}\n"
            self.history_text.insert("1.0", history_entry)
            self.history_text.configure(state="disabled")

        except requests.exceptions.Timeout:
            messagebox.showerror("Erro", "Requisição expirou (timeout)")
        except requests.exceptions.ConnectionError:
            messagebox.showerror("Erro", "Erro de conexão com a API")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao enviar requisição:\n{str(e)}")

    def copy_curl(self):
        if not self.last_response:
            messagebox.showinfo("Info", "Envie uma requisição primeiro")
            return

        endpoint = self.endpoint_var.get()
        url = f"https://app.dabradata.com/api/v1/consulta/{endpoint}"
        
        curl_cmd = f'curl -X POST "{url}"'
        curl_cmd += f' -H "Content-Type: application/json"'
        curl_cmd += f' -H "Authorization: Bearer {self.token}"'
        
        params_str = self.param_text.get("1.0", "end-1c")
        if params_str.strip() and params_str != "{}":
            curl_cmd += f" --data-raw '{params_str}'"
        else:
            curl_cmd += " --data-raw '{}'"

        self.response_text.configure(state="normal")
        self.response_text.delete("1.0", "end")
        self.response_text.insert("end", curl_cmd)
        self.response_text.configure(state="disabled")

        messagebox.showinfo("Sucesso", "CURL copiado para a aba Response!")

    def clear_params(self):
        self.param_text.delete("1.0", "end")
        self.param_text.insert("1.0", "{}")
        self.response_text.configure(state="normal")
        self.response_text.delete("1.0", "end")
        self.response_text.configure(state="disabled")


if __name__ == "__main__":
    app = APITesterApp()
    app.mainloop()
