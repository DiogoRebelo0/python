from flask import Flask, request, render_template_string, session, redirect, url_for, send_file
import json, os, io, datetime
from PIL import Image, ImageDraw, ImageFont

app = Flask(__name__)
app.secret_key = "sandru123"

# senha de admin
ADMIN_KEY = "d4d5c4xc4"

RANKING_PATH = "ranking.json"

# ==========================
# Persistência do ranking
# ==========================
def load_ranking():
    if os.path.exists(RANKING_PATH):
        try:
            with open(RANKING_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                cleaned = []
                for it in data:
                    cleaned.append({
                        "nome": it.get("nome","Anónimo"),
                        "tamanho": int(it.get("tamanho",0)),
                        "grossura": int(it.get("grossura",0)),
                        "sentido": it.get("sentido","D"),
                        "cor1": it.get("cor1", "#ffc0cb"),
                        "cor2": it.get("cor2", "#8b4513"),
                        "score": int(it.get("score",0)),
                        "desenho_html": it.get("desenho_html",""),
                        "created_at": it.get("created_at","")
                    })
                return cleaned
        except Exception:
            return []
    return []

def save_ranking(rk):
    with open(RANKING_PATH, "w", encoding="utf-8") as f:
        json.dump(rk, f, ensure_ascii=False, indent=2)

ranking = load_ranking()

def ordenar_ranking():
    ranking.sort(key=lambda x: (x["score"], x["tamanho"], x["grossura"]), reverse=True)

# ==========================
# Desenho
# ==========================
def gerar_linhas(tamanho, grossura, sentido, cor1, cor2):
    linhas = []
    quartil = max(1, tamanho // 4)
    for i in range(tamanho):
        cor = cor1 if i < quartil else cor2
        if sentido == "E":
            desloc = grossura
        elif sentido == "D":
            desloc = grossura + 1
        else:
            desloc = grossura + 1
        texto = (" " * desloc) + ("∎" * grossura)
        linhas.append((cor, texto))
    for g in range(grossura):
        texto = ("∎" * grossura) + (" " * grossura) + ("∎" * grossura)
        linhas.append((cor2, texto))
    return linhas

def linhas_para_html(linhas):
    return "<br>".join([f'<span style="color:{cor}">{texto}</span>' for cor, texto in linhas])

# ==========================
# PNG
# ==========================
def hex_to_rgb(hx):
    hx = hx.lstrip("#")
    if len(hx) == 3:
        hx = "".join([c*2 for c in hx])
    try:
        return tuple(int(hx[i:i+2], 16) for i in (0, 2, 4))
    except Exception:
        return (255, 255, 255)

def gerar_png(linhas, titulo="Esse é o meu meninão"):
    font = ImageFont.load_default()
    dummy_img = Image.new("RGB", (1, 1))
    dummy_draw = ImageDraw.Draw(dummy_img)

    max_w = 0
    for _, texto in linhas:
        bbox = dummy_draw.textbbox((0, 0), texto, font=font)
        w = bbox[2] - bbox[0]
        if w > max_w:
            max_w = w

    pad_x = 20
    pad_y = 20
    line_h = 16
    title_h = 24
    total_h = pad_y + title_h + 10 + len(linhas) * line_h + pad_y
    total_w = pad_x*2 + max_w

    img = Image.new("RGB", (total_w, total_h), color=(75, 0, 130))
    draw = ImageDraw.Draw(img)

    draw.text((pad_x, pad_y), titulo, fill=(255,255,255), font=font)

    y = pad_y + title_h + 10
    for cor, texto in linhas:
        draw.text((pad_x, y), texto, fill=hex_to_rgb(cor), font=font)
        y += line_h

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf

# ==========================
# Templates principais
# ==========================
HTML_INDEX = """
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>O teu meninão</title>
  <style>
    body { font-family: monospace; background-color: #f0f0f0; margin: 0; padding: 0; }
    h1 { text-align: center; }
    .container { display: flex; gap: 20px; padding: 20px; }
    .left, .right { flex: 1; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 0 10px rgba(0,0,0,0.08); }
    pre { text-align: left; display: inline-block; }
    table { width: 100%; border-collapse: collapse; margin-top: 10px; }
    th, td { border: 1px solid #ccc; padding: 6px 10px; text-align: center; }
    .botao { display: inline-block; padding: 10px 16px; margin-top: 12px; background-color: #E1306C;
             color: white; text-decoration: none; border-radius: 6px; border: none; cursor: pointer; }
    .botao:hover { background-color: #c1275b; }
    .row { margin-bottom: 10px; }
    .inputs { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
    label { display: block; margin-bottom: 4px; }
    input[type="number"], input[type="text"], input[type="color"] { width: 100%; padding: 6px; }
  </style>
</head>
<body>
  <h1>Cria o teu meninão</h1>
  <div class="container">
    <div class="left">
      <form method="post">
        <div class="inputs">
          <div class="row">
            <label>Nome do meninão:</label>
            <input type="text" name="nome" placeholder="Ex.: Sandrão">
          </div>
          <div class="row">
            <label>Tamanho (máx 40):</label>
            <input type="number" name="tamanho" max="40" min="1">
          </div>
          <div class="row">
            <label>Grossura (máx 10):</label>
            <input type="number" name="grossura" max="10" min="1">
          </div>
          <div class="row">
            <label>Sentido (E ou D):</label>
            <input type="text" name="sentido" placeholder="E ou D">
          </div>
          <div class="row">
            <label>Cor primária (topo 25%):</label>
            <input type="color" name="cor1" value="#ffc0cb">
          </div>
          <div class="row">
            <label>Cor secundária (resto):</label>
            <input type="color" name="cor2" value="#8b4513">
          </div>
        </div>
        <button type="submit" class="botao">Desenhar</button>
      </form>

      <div style="margin-top:12px;">
        <pre>{{ desenho|safe }}</pre>
        <p>{{ mensagem }}</p>
      </div>

      {% if desenho %}
        <form method="post" action="{{ url_for('add_ranking') }}">
          <button type="submit" class="botao">Adicionar o meu meninão ao ranking</button>
        </form>
        <a class="botao" href="{{ url_for('postar') }}" target="_blank">Ver o meu meninão</a>
        <a class="botao" href="{{ url_for('download_png') }}" target="_blank">Descarregar PNG</a>
      {% endif %}
    </div>

    <div class="right">
      <h2>Ranking dos Meninões</h2>
      <table>
        <tr>
          <th>#</th><th>Medalha</th><th>Nome</th><th>Tamanho</th><th>Grossura</th><th>Score</th>
        </tr>
        {% for item in ranking %}
          <tr>
            <td>{{ loop.index }}</td>
            <td>
              {% if loop.index == 1 %} 🥇
              {% elif loop.index == 2 %} 🥈
              {% elif loop.index == 3 %} 🥉
              {% else %} —
              {% endif %}
            </td>
            <td>{{ item['nome'] }}</td>
            <td>{{ item['tamanho'] }}</td>
            <td>{{ item['grossura'] }}</td>
            <td>{{ item['score'] }}</td>
          </tr>
        {% endfor %}
      </table>
      <div style="margin-top:12px;">
        <a class="botao" href="{{ url_for('galeria') }}" target="_blank">Ver galeria</a>
      </div>
    </div>
  </div>
</body>
</html>
"""

HTML_POSTAR = """
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Meu Meninão</title>
  <style>
    body { text-align: center; font-family: monospace; background-color: #4B0082; color: white; }
    pre { text-align: center; font-size: 20px; display: inline-block; }
    h1 { margin-top: 50px; }
  </style>
</head>
<body>
  <h1>Esse é o meu meninão</h1>
  <pre>{{ desenho|safe }}</pre><br>
  <p><b>Tira print do teu meninão e posta no teu Insta 📸</b></p>
</body>
</html>
"""

HTML_GALERIA = """
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Galeria dos Meninões</title>
  <style>
    body { font-family: monospace; background: #f6f6ff; margin: 0; padding: 20px; }
    h1 { text-align: center; margin-bottom: 16px; }
    .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 16px; }
    .card { background: white; border-radius: 10px; padding: 14px; box-shadow: 0 0 10px rgba(0,0,0,0.07); }
    .meta { margin-bottom: 8px; font-size: 14px; }
    pre { display: inline-block; }
    .back { display: inline-block; margin-bottom: 12px; }
    .chip { display:inline-block; padding: 2px 8px; border-radius: 999px; background:#eee; font-size: 12px; margin-left:6px; }
  </style>
</head>
<body>
  <div class="back"><a href="{{ url_for('index') }}">← Voltar</a></div>
  <h1>Galeria dos Meninões</h1>
  <div class="grid">
    {% for it in ranking %}
      <div class="card">
        <div class="meta">
          <b>{{ it['nome'] }}</b>
          <span class="chip">T: {{ it['tamanho'] }}</span>
          <span class="chip">G: {{ it['grossura'] }}</span>
          <span class="chip">Score: {{ it['score'] }}</span>
        </div>
        <pre>{{ it['desenho_html']|safe }}</pre>
      </div>
    {% endfor %}
  </div>
</body>
</html>
"""

# ==========================
# Funções auxiliares
# ==========================
def mensagem_final(tamanho):
    if tamanho < 6:
        return "Então é esse o teu meninão... melhor dizendo, o teu menininho! 😂"
    elif tamanho < 15:
        return "Então é esse o teu meninão, não tão grande mas não tão pequeno."
    else:
        return "Então é esse o gigante desacordado? É maior do que a Torre Eiffel!!! 🚀"

# ==========================
# Rotas normais
# ==========================
@app.route("/", methods=["GET", "POST"])
def index():
    desenho_html = ""
    mensagem = ""
    if request.method == "POST":
        nome = (request.form.get("nome") or "").strip()
        tamanho = int(request.form.get("tamanho", 0) or 0)
        grossura = int(request.form.get("grossura", 0) or 0)
        sentido = (request.form.get("sentido") or "").strip().upper() or "D"
        cor1 = (request.form.get("cor1") or "#ffc0cb").strip()
        cor2 = (request.form.get("cor2") or "#8b4513").strip()

        if tamanho > 0 and grossura > 0:
            linhas = gerar_linhas(tamanho, grossura, sentido, cor1, cor2)
            desenho_html = linhas_para_html(linhas)

            session["nome"] = nome if nome else "Anónimo"
            session["tamanho"] = tamanho
            session["grossura"] = grossura
            session["sentido"] = sentido
            session["cor1"] = cor1
            session["cor2"] = cor2
            session["linhas"] = linhas
            session["desenho_html"] = desenho_html
            mensagem = mensagem_final(tamanho)

    return render_template_string(HTML_INDEX,
                                  desenho=desenho_html,
                                  mensagem=mensagem,
                                  ranking=ranking)

@app.route("/add_ranking", methods=["POST"])
def add_ranking():
    if all(k in session for k in ["tamanho","grossura","sentido","cor1","cor2","desenho_html"]):
        tamanho = int(session["tamanho"])
        grossura = int(session["grossura"])
        score = tamanho * grossura
        item = {
            "nome": session.get("nome","Anónimo"),
            "tamanho": tamanho,
            "grossura": grossura,
            "sentido": session.get("sentido","D"),
            "cor1": session.get("cor1","#ffc0cb"),
            "cor2": session.get("cor2","#8b4513"),
            "score": score,
            "desenho_html": session.get("desenho_html",""),
            "created_at": datetime.datetime.utcnow().isoformat() + "Z"
        }
        ranking.append(item)
        ordenar_ranking()
        save_ranking(ranking)
    return redirect(url_for("index"))

@app.route("/postar")
def postar():
    desenho_html = session.get("desenho_html","")
    if not desenho_html:
        return "Não há desenho para mostrar."
    return render_template_string(HTML_POSTAR, desenho=desenho_html)

@app.route("/download_png")
def download_png():
    linhas = session.get("linhas", [])
    if not linhas:
        return "Não há desenho para gerar imagem."
    buf = gerar_png(linhas)
    return send_file(buf, mimetype="image/png", download_name="meninão.png")

@app.route("/galeria")
def galeria():
    return render_template_string(HTML_GALERIA, ranking=ranking)

# ==========================
# Admin
# ==========================
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        senha = request.form.get("senha","")
        if senha == ADMIN_KEY:
            session["is_admin"] = True
            return redirect(url_for("admin"))
        else:
            return "Senha errada!", 403
    return """
    <h1>Login Admin</h1>
    <form method="post">
        <input type="password" name="senha" placeholder="Senha">
        <button type="submit">Entrar</button>
    </form>
    """

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if not session.get("is_admin"):
        return redirect(url_for("admin_login"))

    if request.method == "POST":
        idx = int(request.form.get("idx", -1))
        if 0 <= idx < len(ranking):
            ranking.pop(idx)
            save_ranking(ranking)
            ordenar_ranking()

    return render_template_string("""
    <h1>Painel Admin</h1>
    <table border=1 cellpadding=6>
      <tr><th>#</th><th>Nome</th><th>Tamanho</th><th>Grossura</th><th>Score</th><th>Remover</th></tr>
      {% for item in ranking %}
      <tr>
        <td>{{ loop.index0 }}</td>
        <td>{{ item['nome'] }}</td>
        <td>{{ item['tamanho'] }}</td>
        <td>{{ item['grossura'] }}</td>
        <td>{{ item['score'] }}</td>
        <td>
          <form method="post">
            <input type="hidden" name="idx" value="{{ loop.index0 }}">
            <button type="submit">❌</button>
          </form>
        </td>
      </tr>
      {% endfor %}
    </table>
    """, ranking=ranking)

if __name__ == "__main__":
    ordenar_ranking()
    app.run(debug=True)
