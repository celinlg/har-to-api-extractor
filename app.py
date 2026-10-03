import json
import os
from pathlib import Path
from tkinter import filedialog, messagebox
from urllib.parse import urlparse, parse_qs

import customtkinter as ctk
from tkinter import ttk

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("HAR to API Extractor")
        self.geometry("1200x800")
        self.minsize(1000, 700)

        self.har_path = None
        self.extracted_data = None

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.title_label = ctk.CTkLabel(
            self,
            text="HAR to API Extractor",
            font=("Segoe UI", 24, "bold"),
        )
        self.title_label.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")

        self.top_bar = ctk.CTkFrame(self)
        self.top_bar.grid(row=1, column=0, padx=20, pady=(0, 10), sticky="ew")

        self.select_btn = ctk.CTkButton(
            self.top_bar,
            text="Selecionar arquivo .har",
            command=self.select_har,
            width=220,
            height=36,
        )
        self.select_btn.grid(row=0, column=0, padx=12, pady=12, sticky="w")

        self.generate_btn = ctk.CTkButton(
            self.top_bar,
            text="Gerar JSON",
            command=self.generate_json,
            width=180,
            height=36,
            fg_color="#2f6fed",
            hover_color="#245bc7",
        )
        self.generate_btn.grid(row=0, column=1, padx=12, pady=12, sticky="e")

        self.path_var = ctk.StringVar(value="Nenhum arquivo selecionado")
        self.path_label = ctk.CTkLabel(
            self.top_bar,
            textvariable=self.path_var,
            anchor="w",
            wraplength=800,
        )
        self.path_label.grid(row=1, column=0, columnspan=2, padx=12, pady=(0, 12), sticky="ew")

        # Create notebook (tabbed interface)
        self.notebook = ttk.Notebook(self)
        self.notebook.grid(row=2, column=0, padx=20, pady=(0, 20), sticky="nsew")

        # Tab 1: Resumo
        self.tab_resumo = ctk.CTkFrame(self.notebook)
        self.notebook.add(self.tab_resumo, text="Resumo")

        self.resumo_text = ctk.CTkTextbox(
            self.tab_resumo,
            height=30,
            fg_color="#1b1d22",
            text_color="#f3f5f8",
            border_color="#2d323c",
            corner_radius=10,
        )
        self.resumo_text.pack(fill="both", expand=True, padx=10, pady=10)
        self.resumo_text.insert("end", "Selecione um arquivo .har para começar.\n")

        # Tab 2: Requisições
        self.tab_requests = ctk.CTkFrame(self.notebook)
        self.notebook.add(self.tab_requests, text="Requisições")

        self.requests_frame = ctk.CTkScrollableFrame(self.tab_requests, fg_color="#1b1d22")
        self.requests_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Tab 3: Headers
        self.tab_headers = ctk.CTkFrame(self.notebook)
        self.notebook.add(self.tab_headers, text="Headers")

        self.headers_text = ctk.CTkTextbox(
            self.tab_headers,
            height=30,
            fg_color="#1b1d22",
            text_color="#f3f5f8",
            border_color="#2d323c",
            corner_radius=10,
        )
        self.headers_text.pack(fill="both", expand=True, padx=10, pady=10)

        # Tab 4: Tokens
        self.tab_tokens = ctk.CTkFrame(self.notebook)
        self.notebook.add(self.tab_tokens, text="Tokens")

        self.tokens_text = ctk.CTkTextbox(
            self.tab_tokens,
            height=30,
            fg_color="#1b1d22",
            text_color="#f3f5f8",
            border_color="#2d323c",
            corner_radius=10,
        )
        self.tokens_text.pack(fill="both", expand=True, padx=10, pady=10)

        # Tab 5: CURL
        self.tab_curl = ctk.CTkFrame(self.notebook)
        self.notebook.add(self.tab_curl, text="CURL Commands")

        self.curl_frame = ctk.CTkScrollableFrame(self.tab_curl, fg_color="#1b1d22")
        self.curl_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Tab 6: Responses
        self.tab_responses = ctk.CTkFrame(self.notebook)
        self.notebook.add(self.tab_responses, text="Responses")

        self.responses_text = ctk.CTkTextbox(
            self.tab_responses,
            height=30,
            fg_color="#1b1d22",
            text_color="#f3f5f8",
            border_color="#2d323c",
            corner_radius=10,
        )
        self.responses_text.pack(fill="both", expand=True, padx=10, pady=10)

    def select_har(self):
        file_path = filedialog.askopenfilename(
            title="Selecione o arquivo HAR",
            filetypes=[("HAR / JSON", "*.har *.json"), ("Todos os arquivos", "*.*")]
        )
        if file_path:
            self.har_path = file_path
            self.path_var.set(file_path)
            self.clear_all_tabs()

    def clear_all_tabs(self):
        self.resumo_text.delete("1.0", "end")
        self.resumo_text.insert("end", "Arquivo selecionado. Clique em 'Gerar JSON' para processar.\n")

        for widget in self.requests_frame.winfo_children():
            widget.destroy()

        self.headers_text.delete("1.0", "end")
        self.tokens_text.delete("1.0", "end")

        for widget in self.curl_frame.winfo_children():
            widget.destroy()

        self.responses_text.delete("1.0", "end")

    def generate_json(self):
        if not self.har_path:
            messagebox.showwarning("Aviso", "Selecione um arquivo .har antes.")
            return

        try:
            from extractor import extract_har

            self.extracted_data = extract_har(self.har_path)

            save_path = filedialog.asksaveasfilename(
                defaultextension=".json",
                initialfile=f"{Path(self.har_path).stem}_apis.json",
                filetypes=[("JSON", "*.json")]
            )

            if save_path:
                with open(save_path, "w", encoding="utf-8") as f:
                    json.dump(self.extracted_data, f, ensure_ascii=False, indent=2)
                messagebox.showinfo("Sucesso", f"JSON gerado em: {save_path}")

            # Populate tabs
            self.populate_tabs()

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao processar o HAR:\n{e}")

    def populate_tabs(self):
        if not self.extracted_data:
            return

        # Tab: Resumo
        self.resumo_text.delete("1.0", "end")
        resumo = f"Arquivo: {self.extracted_data['source_file']}\n"
        resumo += f"Total de requisições: {self.extracted_data['total_requests']}\n\n"
        resumo += "Endpoints detectados:\n"

        endpoints = {}
        for req in self.extracted_data['requests']:
            endpoint = f"{req['method']} {req['host']}{req['endpoint']}"
            endpoints[endpoint] = endpoints.get(endpoint, 0) + 1

        for endpoint, count in endpoints.items():
            resumo += f"  {endpoint}\n"

        self.resumo_text.insert("end", resumo)

        # Tab: Requisições
        for widget in self.requests_frame.winfo_children():
            widget.destroy()

        for idx, req in enumerate(self.extracted_data['requests'], start=1):
            req_frame = ctk.CTkFrame(self.requests_frame, fg_color="#2d323c", corner_radius=8)
            req_frame.pack(fill="x", padx=5, pady=5)

            method = req['method']
            color = self.get_method_color(method)

            method_label = ctk.CTkLabel(
                req_frame,
                text=f"{method}",
                font=("Segoe UI", 11, "bold"),
                text_color=color,
                width=60
            )
            method_label.pack(side="left", padx=10, pady=8)

            url_label = ctk.CTkLabel(
                req_frame,
                text=f"{req['host']}{req['endpoint']}",
                font=("Segoe UI", 10),
                text_color="#e0e0e0",
                anchor="w"
            )
            url_label.pack(side="left", fill="x", expand=True, padx=5, pady=8)

        # Tab: Headers
        self.headers_text.delete("1.0", "end")
        headers_content = "HEADERS ENCONTRADOS:\n\n"
        all_headers = {}

        for req in self.extracted_data['requests']:
            for key, val in req['headers'].items():
                if key not in all_headers:
                    all_headers[key] = []
                all_headers[key].append(val)

        for header, values in all_headers.items():
            headers_content += f"{header}:\n"
            for val in set(values):
                headers_content += f"  - {val}\n"
            headers_content += "\n"

        self.headers_text.insert("end", headers_content)

        # Tab: Tokens
        self.tokens_text.delete("1.0", "end")
        tokens_content = "TOKENS EXTRAÍDOS:\n\n"
        all_tokens = {}

        for req in self.extracted_data['requests']:
            for key, val in req['tokens'].items():
                if key not in all_tokens:
                    all_tokens[key] = []
                if val not in all_tokens[key]:
                    all_tokens[key].append(val)

        if all_tokens:
            for token_name, values in all_tokens.items():
                tokens_content += f"{token_name}:\n"
                for val in values:
                    # Mask sensitive data
                    masked = self.mask_token(val)
                    tokens_content += f"  - {masked}\n"
                tokens_content += "\n"
        else:
            tokens_content += "Nenhum token detectado.\n"

        self.tokens_text.insert("end", tokens_content)

        # Tab: CURL
        for widget in self.curl_frame.winfo_children():
            widget.destroy()

        for idx, req in enumerate(self.extracted_data['requests'], start=1):
            curl_cmd = req['curl']

            curl_box = ctk.CTkFrame(self.curl_frame, fg_color="#2d323c", corner_radius=8)
            curl_box.pack(fill="x", padx=5, pady=5)

            label = ctk.CTkLabel(
                curl_box,
                text=f"Request #{idx} - {req['method']} {req['endpoint']}",
                font=("Segoe UI", 10, "bold"),
                text_color="#2f6fed"
            )
            label.pack(anchor="w", padx=10, pady=(8, 2))

            text_box = ctk.CTkTextbox(
                curl_box,
                height=4,
                fg_color="#1b1d22",
                text_color="#f3f5f8",
                border_color="#444",
                corner_radius=6
            )
            text_box.pack(fill="x", padx=10, pady=(0, 8))
            text_box.insert("end", curl_cmd)
            text_box.configure(state="disabled")

        # Tab: Responses
        self.responses_text.delete("1.0", "end")
        responses_content = "RESPOSTAS HTTP:\n\n"

        for idx, req in enumerate(self.extracted_data['requests'], start=1):
            responses_content += f"--- Request #{idx} ---\n"
            responses_content += f"Method: {req['method']} {req['endpoint']}\n"
            responses_content += f"Status: {req['response']['status']} {req['response']['status_text']}\n\n"

            if req['response']['body']:
                responses_content += "Response Body:\n"
                if isinstance(req['response']['body'], dict):
                    responses_content += json.dumps(req['response']['body'], ensure_ascii=False, indent=2)
                else:
                    responses_content += str(req['response']['body'])
            else:
                responses_content += "No response body\n"

            responses_content += "\n\n"

        self.responses_text.insert("end", responses_content)

    def get_method_color(self, method):
        colors = {
            "GET": "#4CAF50",
            "POST": "#2196F3",
            "PUT": "#FF9800",
            "DELETE": "#F44336",
            "PATCH": "#9C27B0",
        }
        return colors.get(method, "#FFFFFF")

    def mask_token(self, token):
        if isinstance(token, str) and len(token) > 20:
            return token[:10] + "..." + token[-10:]
        return token


if __name__ == "__main__":
    app = App()
    app.mainloop()
