import streamlit as st
import pandas as pd
import csv
import os
import requests
import base64

def new_id(old_id):
    mapping = {
        "fun": "fun",
        "swi": "swi",
        "zw": "zwi",
        "pk": "pik",
        "lz": "luz",
        "ps": "pre",
        "wol": "wol",
        "dyl": "dyl"
    }
    return mapping.get(old_id, old_id)

def save_row(row, file_path):
    file_exists = os.path.exists(file_path)
    with open(file_path, "a", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter=";")
        if not file_exists:
            header = ["id", "text", "category", "left", "right"]
            writer.writerow(header)
        writer.writerow(row)

def upload_to_github(file_path, repo, path_in_repo, token, commit_message):
    with open(file_path, "rb") as f:
        content = f.read()
    b64_content = base64.b64encode(content).decode("utf-8")

    url = f"https://api.github.com/repos/{repo}/contents/{path_in_repo}"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    res_get = requests.get(url, headers=headers)
    sha = res_get.json().get("sha") if res_get.status_code == 200 else None
    data = {
        "message": commit_message,
        "content": b64_content,
        "branch": "main"
    }
    if sha:
        data["sha"] = sha 

    response = requests.put(url, headers=headers, json=data)
    return response


# --- START ---
if "step" not in st.session_state:
    st.session_state.step = "start"

if st.session_state.step == "start":
    st.title("📋 Walidacja pytań")

    if st.button("➕ Dodawanie nowych pytań"):
        st.session_state.step = "new_que_edit"
        st.rerun()

    if st.button("✅ Walidacja pytań gotowych"):
        st.session_state.step = "ready_val"
        st.rerun()


# --- WALIDACJA PYTAŃ GOTOWYCH ---
elif st.session_state.step == "ready_val":
    st.subheader("✅ Walidacja pytań gotowych")

    # przycisk upload do GitHuba
    if st.button("💾 Zapisz na GitHub"):
        repo = "DawidS25/walidacja_pytan"
        files = {
            "que_ready.csv": "que_ready.csv",
            "que_accepted.csv": "que_accepted.csv",
            "que_to_edit.csv": "que_to_edit.csv"
        }
        commit_message = "Aktualizacja pytań przez Streamlit"
        try:
            token = st.secrets["GITHUB_TOKEN"]
        except Exception:
            token = None

        if token:
            for file_path, path_in_repo in files.items():
                if os.path.exists(file_path):
                    res = upload_to_github(file_path, repo, path_in_repo, token, commit_message)
                    if res.status_code in (200, 201):
                        st.success(f"✅ Plik {file_path} został zapisany na GitHub!")
                    else:
                        st.error(f"❌ Błąd zapisu {file_path}: {res.status_code} – {res.text}")
        else:
            st.warning("⚠️ Brak tokenu GITHUB_TOKEN w Secrets Streamlit.")

    df_ready = pd.read_csv("que_ready.csv", sep=";")

    if df_ready.empty:
        st.info("🎉 Brak pytań w pliku que_ready.csv")
        if st.button("↩️ Powrót"):
            st.session_state.step = "start"
            st.rerun()
        st.stop()

    if "row" not in st.session_state:
        st.session_state.row = df_ready.sample(n=1).iloc[0].tolist()

    row = st.session_state.row
    st.warning(
        f"**Pytanie:**  \n"
        f"📚 {row[2]} (🆔{row[0]})  \n"
        f"##### **{row[1]}**  \n"
        f"⬅️ {row[3]} | {row[4]} ➡️  \n"
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("✅ Zatwierdź"):
            save_row(row, "que_accepted.csv")
            df_ready = df_ready[df_ready["id"] != row[0]]
            df_ready.to_csv("que_ready.csv", sep=";", index=False)
            del st.session_state.row
            st.rerun()

    with col2:
        if st.button("✍️ Do zmiany"):
            save_row(row, "que_to_edit.csv")
            df_ready = df_ready[df_ready["id"] != row[0]]
            df_ready.to_csv("que_ready.csv", sep=";", index=False)
            del st.session_state.row
            st.rerun()

    with col3:
        if st.button("❌ Odrzuć"):
            df_ready = df_ready[df_ready["id"] != row[0]]
            df_ready.to_csv("que_ready.csv", sep=";", index=False)
            del st.session_state.row
            st.rerun()

    if st.button("↩️ Powrót"):
        if "row" in st.session_state:
            del st.session_state.row
        st.session_state.step = "start"
        st.rerun()


# --- DODAWANIE NOWYCH PYTAŃ ---
elif st.session_state.step == "new_que_edit":
    st.subheader("➕ Dodawanie nowych pytań")

    # przycisk upload do GitHuba
    if st.button("💾 Zapisz na GitHub"):
        repo = "DawidS25/walidacja_pytan"
        files = {
            "que_new.csv": "que_new.csv",
            "que_new_ready.csv": "que_new_ready.csv"
        }
        commit_message = "Aktualizacja pytań przez Streamlit"
        try:
            token = st.secrets["GITHUB_TOKEN"]
        except Exception:
            token = None

        if token:
            for file_path, path_in_repo in files.items():
                if os.path.exists(file_path):
                    res = upload_to_github(file_path, repo, path_in_repo, token, commit_message)
                    if res.status_code in (200, 201):
                        st.success(f"✅ Plik {file_path} został zapisany na GitHub!")
                    else:
                        st.error(f"❌ Błąd zapisu {file_path}: {res.status_code} – {res.text}")
        else:
            st.warning("⚠️ Brak tokenu GITHUB_TOKEN w Secrets Streamlit.")

    df_to_val = pd.read_csv('que_new.csv', sep=';')
    df_new_ready = pd.read_csv('que_new_ready.csv', sep=';')

    if len(df_to_val) <= 0:
        st.info(f"🎉 Wszystkie pytania zostały już zwalidowane! {len(df_new_ready)} nowych pytań!") 
        if st.button("↩️ Powrót"):
            st.session_state.step = "start"
            st.rerun()
        st.stop()
    else:
        if "row" not in st.session_state:
            st.session_state.row = df_to_val.iloc[0].tolist()
    st.markdown(f"Pozostało {len(df_to_val)} pytań. Dodano {len(df_new_ready)} nowych pytań")
    row = st.session_state.row
    row[0] = new_id("".join([c for c in row[0] if c.isalpha()]))
    st.text_input(f"🆔 ID: ", value=row[0], key = "ID")
    st.text_input("📚 Kategoria:", value=row[2], key="category")
    st.text_input("❓ Pytanie:", value=row[1], key="question")
    st.text_input("⬅️ Lewo:", value=row[3], key="left")
    st.text_input("➡️ Prawo:", value=row[4], key="right")

    if st.button("💾 Zatwierdź zmiany"):
        edited_row = [
            st.session_state.ID.strip(),
            st.session_state.question,
            st.session_state.category.strip(),
            st.session_state.left,
            st.session_state.right
        ]
        row_to_import = [
            f"{edited_row[0]}000",
            edited_row[1],
            edited_row[2],
            edited_row[3],
            edited_row[4]
        ]
        save_row(row_to_import, "que_new_ready.csv")
        df_to_val = df_to_val.drop(df_to_val.index[0])
        df_to_val.to_csv('que_new.csv', index=False, sep=';')            
        del st.session_state.row
        st.rerun()

    if st.button("❌ Odrzuć pytanie"):
        df_to_val = df_to_val.drop(df_to_val.index[0])
        df_to_val.to_csv('que_new.csv', index=False, sep=';')
        del st.session_state.row
        st.rerun()

    if st.button("↩️ Powrót"):
        if "row" in st.session_state:
            del st.session_state.row
        st.session_state.step = "start"
        st.rerun()


elif st.session_state.step == "new_que":
    st.text_area(
        "Wprowadź nowe pytania do walidacji w postaci .csv",
        value = "",
        key = "new_que"
    )
    if st.button("💾 Dopisz te pytania do pliku CSV"):
        with open("que_new.csv", "a", encoding="utf-8") as f:
            f.write("\n" + st.session_state.new_que.strip())
        st.success("✅ Plik que_new.csv został zapisany lokalnie!")
    if st.button("↩️ Powrót"):
        st.session_state.step = "new_que_edit"
        st.rerun()