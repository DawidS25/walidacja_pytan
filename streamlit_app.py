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

def save_to_ready(row_to_import, file_path):
    parts = row_to_import.strip().split(";")
    old_id = parts[0]  # np. 'dyl000'
    prefix = "".join([c for c in old_id if c.isalpha()])  # pierwsze 3 litery
    max_number = 0
    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        with open(file_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter=";")
            for row in reader:
                row_id = row.get("id", "")
                row_prefix = "".join([c for c in row_id if c.isalpha()])
                row_number = "".join([c for c in row_id if c.isdigit()])
                if row_prefix == prefix:
                    max_number = max(max_number, int(row_number))
    new_number = max_number + 1
    parts[0] = f"{prefix}{new_number:03d}"
    file_exists = os.path.exists(file_path)
    with open(file_path, "a", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter=";")
        if not file_exists:
            header = ["id", "text", "category", "left", "right"]
            writer.writerow(header)
        writer.writerow(parts)

def save_to_used(orginal_row_to_import):
    file_path = "que_used.csv"
    with open(file_path, "a", encoding="utf-8", newline="") as f:
        f.write(orginal_row_to_import.strip() + "\n")

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


if "step" not in st.session_state:
    st.session_state.step = "editor"

if st.session_state.step == "editor":
    # --- Przycisk do zapisu CSV na GitHub ---
    if st.button("💾 Zapisz na GitHub"):
        repo = "DawidS25/walidacja_pytan"
        file_path = "que_used.csv"
        path_in_repo = "que_used.csv"
        file_path_2 = "que_ready.csv"
        path_in_repo_2 = "que_ready.csv"
        commit_message = "Aktualizacja pytań przez Streamlit"

        try:
            token = st.secrets["GITHUB_TOKEN"]
        except Exception:
            token = None

        if token:
            res = upload_to_github(file_path, repo, path_in_repo, token, commit_message)
            res_2 = upload_to_github(file_path_2, repo, path_in_repo_2, token, commit_message)
            if res.status_code in (200, 201):
                st.success("✅ Plik que_used.csv został zapisany na GitHub!")
            else:
                st.error(f"❌ Błąd zapisu que_used.csv: {res.status_code} – {res.text}")
            if res_2.status_code in (200, 201):
                st.success("✅ Plik que_ready.csv został zapisany na GitHub!")
            else:
                st.error(f"❌ Błąd zapisu que_ready.csv: {res_2.status_code} – {res_2.text}")
        else:
            st.warning("⚠️ Brak tokenu GITHUB_TOKEN w Secrets Streamlit.")

    df_all = pd.read_csv('que_to_val.csv', sep=';')
    df_used = pd.read_csv('que_used.csv', sep=';')
    df_to_val = df_all[~df_all["id"].isin(df_used["id"])]

    st.markdown(f"Zwalidowano {len(df_used)} z {len(df_all)} pytań. Zostało {len(df_to_val)} do końca.")
    if df_to_val.empty:
        st.info("🎉 Wszystkie pytania zostały już zwalidowane!")
    else:
        if "row" not in st.session_state:
            st.session_state.row = df_to_val.sample(n=1).iloc[0].tolist()
            st.session_state.orginal_row = st.session_state.row.copy()
    row = st.session_state.row
    if len(row) == 3:
        row.append("NIE")
        row.append("TAK")
    row[0] = new_id("".join([c for c in row[0] if c.isalpha()]))
    orginal_row = st.session_state.orginal_row
    orginal_row_to_import = f"{orginal_row[0]};{orginal_row[1]};{orginal_row[2]}"
    if "orginal_row_to_import" not in st.session_state:
        st.session_state.orginal_row_to_import = orginal_row_to_import

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
        if "edited_row" not in st.session_state:
            st.session_state.edited_row = edited_row
        else:
            st.session_state.edited_row = edited_row
        row_to_import = f"{edited_row[0]}000;{edited_row[1]};{edited_row[2]};{edited_row[3]};{edited_row[4]}"
        if "row_to_import" not in st.session_state:
            st.session_state.row_to_import = row_to_import
        else:
            st.session_state.row_to_import = row_to_import
        st.session_state.row = edited_row
        st.session_state.step = "walidacja"
        st.rerun()
    if st.button("❌ Odrzuć pytanie"):
        save_to_used(orginal_row_to_import)
        del st.session_state.row
        del st.session_state.orginal_row
        del st.session_state.orginal_row_to_import
        if "edited_row" in st.session_state:
            del st.session_state.edited_row
        if "row_to_import" in st.session_state:
            del st.session_state.row_to_import
        del st.session_state.step
        st.rerun()
    if st.button("✍️ Nowe pytania"):
        del st.session_state.row
        del st.session_state.orginal_row
        del st.session_state.orginal_row_to_import
        if "edited_row" in st.session_state:
            del st.session_state.edited_row
        if "row_to_import" in st.session_state:
            del st.session_state.row_to_import
        del st.session_state.step
        st.session_state.step = "new_que_edit"
        st.rerun()

elif st.session_state.step == "walidacja":
    edited_row = st.session_state.edited_row
    row_to_import = st.session_state.row_to_import
    orginal_row_to_import = st.session_state.orginal_row_to_import
    st.warning(
        f"**Pytanie:**  \n"
        f"📚 {edited_row[2]} (🆔{edited_row[0]}000)  \n"
        f"##### **{edited_row[1]}**  \n"
        f"⬅️ {edited_row[3]} | {edited_row[4]} ➡️  \n"
        f"*{row_to_import}*"
    )
    col1, col2 = st.columns(2)
    with col1:
        if st.button("↩️ Edytuj"):
            st.session_state.step = "editor"
            st.rerun()
    with col2:
        if st.button("✅ Zapisz pytanie"):
            save_to_ready(row_to_import, "que_ready.csv")
            save_to_used(orginal_row_to_import)
            del st.session_state.row
            del st.session_state.orginal_row
            del st.session_state.orginal_row_to_import
            del st.session_state.edited_row
            del st.session_state.row_to_import
            del st.session_state.step
            st.rerun()


elif st.session_state.step == "new_que_edit":
    df_to_val = pd.read_csv('que_new.csv', sep=';')
    df_new_ready = pd.read_csv('que_new_ready.csv', sep=';')

    col1, col2 = st.columns(2)
    with col1:
        if st.button("💾 Zapisz na GitHub"):
            repo = "DawidS25/walidacja_pytan"
            file_path = "que_new.csv"
            path_in_repo = "que_new.csv"
            file_path_2 = "que_new_ready.csv"
            path_in_repo_2 = "que_new_ready.csv"
            commit_message = "Aktualizacja pytań przez Streamlit"

            try:
                token = st.secrets["GITHUB_TOKEN"]
            except Exception:
                token = None

            if token:
                res = upload_to_github(file_path, repo, path_in_repo, token, commit_message)
                res_2 = upload_to_github(file_path_2, repo, path_in_repo_2, token, commit_message)
                if res.status_code in (200, 201):
                    st.success("✅ Plik que_new.csv został zapisany na GitHub!")
                else:
                    st.error(f"❌ Błąd zapisu que_new.csv: {res.status_code} – {res.text}")
                if res_2.status_code in (200, 201):
                    st.success("✅ Plik que_new_ready.csv został zapisany na GitHub!")
                else:
                    st.error(f"❌ Błąd zapisu que_new_ready.csv: {res_2.status_code} – {res_2.text}")
            else:
                st.warning("⚠️ Brak tokenu GITHUB_TOKEN w Secrets Streamlit.")
    with col2:
        if st.button("➕ Dodaj nowe pytania"):
            st.session_state.step = "new_que"
            st.rerun()

    if len(df_to_val) <= 0:
        st.info(f"🎉 Wszystkie pytania zostały już zwalidowane! {len(df_new_ready)} nowych pytań!") 
        if st.button("↩️ Powrót"):
            if "row" in st.session_state:
                del st.session_state.row
            if "edited_row" in st.session_state:
                del st.session_state.edited_row
            if "row_to_import" in st.session_state:
                del st.session_state.row_to_import
            st.session_state.step = "editor"
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
        if "edited_row" not in st.session_state:
            st.session_state.edited_row = edited_row
        else:
            st.session_state.edited_row = edited_row
        row_to_import = f"{edited_row[0]}000;{edited_row[1]};{edited_row[2]};{edited_row[3]};{edited_row[4]}"
        if "row_to_import" not in st.session_state:
            st.session_state.row_to_import = row_to_import
        else:
            st.session_state.row_to_import = row_to_import
            st.session_state.row = edited_row
        st.session_state.step = "new_que_val"
        st.rerun()
    if st.button("❌ Odrzuć pytanie"):
        df_to_val = df_to_val.drop(df_to_val.index[0])
        df_to_val.to_csv('que_new.csv', index=False, sep=';')
        del st.session_state.row
        if "edited_row" in st.session_state:
            del st.session_state.edited_row
        if "row_to_import" in st.session_state:
            del st.session_state.row_to_import
        st.session_state.step = "new_que_edit"
        st.rerun()
    if st.button("↩️ Powrót"):
        if "row" in st.session_state:
            del st.session_state.row
        if "edited_row" in st.session_state:
            del st.session_state.edited_row
        if "row_to_import" in st.session_state:
            del st.session_state.row_to_import
        st.session_state.step = "editor"
        st.rerun()

elif st.session_state.step == "new_que_val":
    edited_row = st.session_state.edited_row
    row_to_import = st.session_state.row_to_import
    st.warning(
        f"**Pytanie:**  \n"
        f"📚 {edited_row[2]} (🆔{edited_row[0]}000)  \n"
        f"##### **{edited_row[1]}**  \n"
        f"⬅️ {edited_row[3]} | {edited_row[4]} ➡️  \n"
        f"*{row_to_import}*"
    )
    col1, col2 = st.columns(2)
    with col1:
        if st.button("↩️ Edytuj"):
            st.session_state.step = "new_que_edit"
            st.rerun()
    with col2:
        if st.button("✅ Zapisz pytanie"):
            save_to_ready(row_to_import, "que_new_ready.csv")
            df_to_val = pd.read_csv('que_new.csv', sep=';')
            df_to_val = df_to_val.drop(df_to_val.index[0])
            df_to_val.to_csv('que_new.csv', index=False, sep=';')            
            del st.session_state.row
            del st.session_state.edited_row
            del st.session_state.row_to_import
            st.session_state.step = "new_que_edit"
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

# git pull origin main --rebase
# git add .
# git commit -m ""
# git push