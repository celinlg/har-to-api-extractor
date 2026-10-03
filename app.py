import json
import os
from urllib.parse import urlparse, parse_qs
from pathlib import Path
import customtkinter as ctk
from tkinter import filedialog, messagebox

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("HAR to API Extractor")
        self.geometry("1100x760")
        self.minsize(900, 620)

        self.har_path = None

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
        self.top_bar.grid_columnconfigure(0, weight=1)
        self.top_bar.grid_columnconfigure(1, weight=0)

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
            wraplength=900,
        )
        self.path_label.grid(row=1, column=0, columnspan=2, padx=12, pady=(0, 12), sticky="ew")

        self.output = ctk.CTkTextbox(
            self,
            height=40,
            fg_color="#1b1d22",
            text_color="#f3f5f8",
            border_color="#2d323c",
            corner_radius=10,
            wrap="word",
        )
        self.output.grid(row=2, column=0, padx=20, pady=(0, 20), sticky="nsew")

        self.output.insert("end", "Selecione um arquivo .har para começar.\n")

    def select_har(self):
        file_path = filedialog.askopenfilename(
            title="Selecione o arquivo HAR",
            filetypes=[("HAR / JSON", "*.har *.json"), ("Todos os arquivos", "*.*")]
        )
        if file_path:
            self.har_path = file_path
            self.path_var.set(file_path)
            self.output.delete("1.0", "end")
            self.output.insert("end", f"Arquivo selecionado: {file_path}\n")

    def generate_json(self):
        if not self.har_path:
            messagebox.showwarning("Aviso", "Selecione um arquivo .har antes.")
            return

        try:
            data = extract_har(self.har_path)
            save_path = filedialog.asksaveasfilename(
                defaultextension=".json",
                initialfile=f"{Path(self.har_path).stem}_apis.json",
                filetypes=[("JSON", "*.json")]
            )

            if not save_path:
                return

            with open(save_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            preview = json.dumps(data, ensure_ascii=False, indent=2)
            self.output.delete("1.0", "end")
            self.output.insert("end", f"Arquivo salvo em: {save_path}\n\n")
            self.output.insert("end", preview[:20000])

            messagebox.showinfo("Sucesso", f"JSON gerado em: {save_path}")

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao processar o HAR:\n{e}")


def get_headers(headers):
    result = {}
    if not headers:
        return result
    for h in headers:
        if isinstance(h, dict):
            name = h.get("name")
            val = h.get("value")
            if name:
                result[name] = val
    return result


def get_query_params(raw_url):
    parsed = urlparse(raw_url)
    params = parse_qs(parsed.query, keep_blank_values=True)
    out = {}
    for k, v in params.items():
        out[k] = v[0] if len(v) == 1 else v
    return out


def build_curl(method, url, headers, body=None):
    parts = [f"curl -X {method} '{url}'"]
    for key, value in headers.items():
        if value is not None and value != "":
            parts.append(f" -H '{key}: {value}'")

    if body is not None:
        if isinstance(body, (dict, list)):
            body_json = json.dumps(body, ensure_ascii=False)
            parts.append(f" --data-raw '{body_json}'")
        else:
            parts.append(f" --data-raw '{str(body)}'")
    return "".join(parts).strip()


def find_tokens(headers, body, query_params):
    found = {}
    token_like = ["authorization", "token", "api-key", "x-api-key", "apikey", "cookie", "jwt", "secret", "sessionid"]

    for key, value in headers.items():
        lower = key.lower()
        if lower in token_like or "token" in lower or "auth" in lower or "key" in lower or "cookie" in lower:
            found[key] = value

    if isinstance(body, dict):
        for key, value in body.items():
            lower = key.lower()
            if lower in token_like or "token" in lower or "auth" in lower or "key" in lower:
                found[f"body.{key}"] = value

    for key, value in query_params.items():
        lower = key.lower()
        if lower in token_like or "token" in lower or "auth" in lower or "key" in lower:
            found[f"query.{key}"] = value

    return found


def extract_har(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        har = json.load(f)

    entries = har.get("log", {}).get("entries", [])
    output = {
        "source_file": os.path.basename(file_path),
        "total_requests": len(entries),
        "requests": []
    }

    for index, entry in enumerate(entries, start=1):
        request = entry.get("request", {})
        response = entry.get("response", {})

        url = request.get("url", "")
        method = request.get("method", "GET")
        parsed = urlparse(url)
        query_params = get_query_params(url)
        headers = get_headers(request.get("headers", []))
        body = None

        post_data = request.get("postData")
        if post_data:
            if isinstance(post_data, dict):
                text = post_data.get("text")
                if text:
                    try:
                        body = json.loads(text)
                    except Exception:
                        body = text
            elif isinstance(post_data, str):
                try:
                    body = json.loads(post_data)
                except Exception:
                    body = post_data

        response_headers = get_headers(response.get("headers", []))
        response_content = response.get("content", {})
        response_body = None
        if isinstance(response_content, dict):
            text = response_content.get("text")
            if text:
                try:
                    response_body = json.loads(text)
                except Exception:
                    response_body = text
        elif isinstance(response_content, str):
            response_body = response_content

        token_values = find_tokens(headers, body, query_params)

        req = {
            "index": index,
            "method": method,
            "url": url,
            "endpoint": parsed.path,
            "host": parsed.netloc,
            "scheme": parsed.scheme,
            "query_params": query_params,
            "headers": headers,
            "body": body,
            "tokens": token_values,
            "response": {
                "status": response.get("status"),
                "status_text": response.get("statusText"),
                "headers": response_headers,
                "body": response_body,
            },
            "curl": build_curl(method, url, headers, body)
        }

        output["requests"].append(req)

    return output


if __name__ == "__main__":
    app = App()
    app.mainloop()
