import streamlit as st
import pandas as pd
import csv
import os
import requests
import base64

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

    if st.button("✅ Walidacja pytań"):
        st.session_state.step = "ready_val"
        st.rerun()
    
    if st.button("✍️ Edycja pytań"):
        st.session_state.step = "edit_que_to_edit"
        st.rerun()

    if st.button("👀 Podgląd pytań"):
        st.session_state.step = "show_que"
        st.rerun()

    df_ready = pd.read_csv("que_ready.csv", sep=";")
    df_accepted = pd.read_csv("que_accepted.csv", sep=";")
    df_to_edit = pd.read_csv("que_to_edit.csv", sep=";")
    
    st.markdown(f"✅: {len(df_accepted)} | ❓: {len(df_ready)} | ✍️: {len(df_to_edit)}")

# --- WALIDACJA PYTAŃ GOTOWYCH ---
elif st.session_state.step == "ready_val":
    st.subheader("✅ Walidacja pytań")

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
    if st.button("➕ Dodaj nowe pytania"):
        st.session_state.step = "new_que"
        st.rerun()

    df_ready = pd.read_csv("que_ready.csv", sep=";")
    df_accepted = pd.read_csv("que_accepted.csv", sep=";")
    df_to_edit = pd.read_csv("que_to_edit.csv", sep=";")

    if df_ready.empty:
        st.info("🎉 Brak pytań w pliku que_ready.csv")
        if st.button("↩️ Powrót"):
            st.session_state.step = "start"
            st.rerun()
        st.stop()

    if "row" not in st.session_state:
        st.session_state.row = df_ready.sample(n=1).iloc[0].tolist()

    row = st.session_state.row
    st.markdown(f"Do zrobienia: {len(df_ready)} | Zaakceptowane: {len(df_accepted)} | Do Edycji: {len(df_to_edit)}")
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
elif st.session_state.step == "new_que":
    st.text_area(
        "Wprowadź nowe pytania do walidacji w postaci .csv",
        value = "",
        key = "new_que"
    )
    if st.button("💾 Dopisz te pytania do pliku CSV"):
        with open("que_ready.csv", "a", encoding="utf-8") as f:
            f.write("\n" + st.session_state.new_que.strip())
        st.success("✅ Plik que_ready.csv został zapisany lokalnie!")
    if st.button("↩️ Powrót"):
        st.session_state.step = "ready_val"
        st.rerun()

# --- EDYCJA PYTAŃ Z que_to_edit ---
elif st.session_state.step == "edit_que_to_edit":
    st.subheader("✍️ Edycja pytań do poprawki")

    if st.button("💾 Zapisz na GitHub"):
        repo = "DawidS25/walidacja_pytan"
        files = {
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

    df_to_edit = pd.read_csv("que_to_edit.csv", sep=";")

    if df_to_edit.empty:
        st.info("🎉 Brak pytań w pliku que_to_edit.csv")
        if st.button("↩️ Powrót"):
            st.session_state.step = "start"
            st.rerun()
        st.stop()

    if "row" not in st.session_state:
        st.session_state.row = df_to_edit.sample(n=1).iloc[0].tolist()

    row = st.session_state.row
    st.markdown(f"Pozostało {len(df_to_edit)} pytań do edycji")

    st.text_input("🆔 ID:", value=row[0], key="edit_ID")
    st.text_input("📚 Kategoria:", value=row[2], key="edit_category")
    st.text_input("❓ Pytanie:", value=row[1], key="edit_question")
    st.text_input("⬅️ Lewo:", value=row[3], key="edit_left")
    st.text_input("➡️ Prawo:", value=row[4], key="edit_right")

    if st.button("👀 Zobacz zmiany"):
        edited_row = [
            st.session_state.edit_ID.strip(),
            st.session_state.edit_question.strip(),
            st.session_state.edit_category.strip(),
            st.session_state.edit_left.strip(),
            st.session_state.edit_right.strip()
        ]
        st.session_state.row = edited_row
        st.session_state.edited_row = edited_row
        st.session_state.step = "que_to_edit_val"
        st.rerun()

    if st.button("↩️ Powrót"):
        if "row" in st.session_state:
            del st.session_state.row
        st.session_state.step = "ready_val"
        st.rerun()


# --- WALIDACJA POPRAWIONEGO PYTANIA ---
elif st.session_state.step == "que_to_edit_val":
    st.subheader("👀 Walidacja poprawionego pytania")

    if "edited_row" not in st.session_state:
        st.warning("⚠️ Brak pytania do walidacji")
        st.session_state.step = "edit_que_to_edit"
        st.rerun()

    row = st.session_state.edited_row
    st.warning(
        f"**Pytanie (po edycji):**  \n"
        f"📚 {row[2]} (🆔{row[0]})  \n"
        f"##### **{row[1]}**  \n"
        f"⬅️ {row[3]} | {row[4]} ➡️  \n"
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Akceptuj"):
            save_row(row, "que_accepted.csv")

            # usuń z que_to_edit
            df_to_edit = pd.read_csv("que_to_edit.csv", sep=";")
            df_to_edit = df_to_edit[df_to_edit["id"] != row[0]]
            df_to_edit.to_csv("que_to_edit.csv", sep=";", index=False)

            del st.session_state.row
            del st.session_state.edited_row
            st.session_state.step = "edit_que_to_edit"
            st.rerun()

    with col2:
        if st.button("↩️ Powrót do edycji"):
            st.session_state.step = "edit_que_to_edit"
            st.rerun()

elif st.session_state.step == "show_que":
    st.markdown(f"## 👀 Podgląd pytań")
    if "step_show" not in st.session_state:
        st.session_state.step_show = None
    if st.button("🔍 Do sprawdzenia"):
        st.session_state.step_show = "ready"
        st.rerun()
    if st.button("✅ Zaakceptowane"):
        st.session_state.step_show = "accepted"
        st.rerun()
    if st.button("✍️ Do zmiany"):
        st.session_state.step_show = "to_edit"
        st.rerun()

    file_map = {
        "ready": "que_ready.csv",
        "accepted": "que_accepted.csv",
        "to_edit": "que_to_edit.csv"
    }

    if st.session_state.step_show in file_map:
        file_path = file_map[st.session_state.step_show]
        df = pd.read_csv(file_path, sep=";")
        st.markdown(f"### 📄 {file_path}")
        edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True)
        if st.button("🔢 Segreguj pytania po ID"):
            # Wyciągamy prefix literowy z ID
            prefix = df["id"].str.extract(r"^([A-Za-z]+)")[0].str.lower()

            # Tworzymy kopię df i numerujemy w kolejności pojawiania się w df
            df = df.copy()
            df["id"] = prefix + (prefix.groupby(prefix).cumcount() + 1).astype(str).str.zfill(3)

            # Nadpisujemy edited_df, żeby zmiany były widoczne w data_editor
            edited_df[:] = df

            # Zapis do pliku
            df.to_csv(file_path, sep=";", index=False)
            st.success(f"✅ Posegregowano i ponumerowano ID w formacie AAA000 od 001 dla każdego prefixu")
            st.rerun()
       
        if st.button("💾 Zapisz zmiany w pliku CSV"):
            edited_df.to_csv(file_path, sep=";", index=False)
            st.success(f"✅ Zapisano zmiany w {file_path}")
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
    if st.button("↩️ Powrót"):
        st.session_state.step = "start"
        if "step_show" in st.session_state:
            del st.session_state.step_show
        st.rerun()