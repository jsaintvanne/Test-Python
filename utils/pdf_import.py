import re
from datetime import datetime
import pandas as pd
import pdfplumber
from typing import Dict, List, Optional, Tuple

# Utility functions kept in this module to keep the page code lean.


def _clean_number(value) -> Optional[float]:
    """Convert diverse numeric formats ("1 234,56", "-1.234,56€") to float.

    Returns None when conversion fails.
    """
    if value is None:
        return None
    try:
        text = str(value)
        if not text.strip():
            return None
        text = text.replace("\u00a0", " ").strip()
        # Handle accounting style amounts like (123,45)
        negative = text.startswith("(") and text.endswith(")")
        # Remove currency and spacing
        cleaned = (
            text.replace(" ", "")
            .replace("€", "")
            .replace(",", ".")
            .replace("(", "")
            .replace(")", "")
        )
        if not cleaned:
            return None
        number = float(cleaned)
        if negative:
            number = -number
        return number
    except Exception:
        return None


def _headerize(df_raw: pd.DataFrame) -> pd.DataFrame:
    """Use the first row as header when it looks like labels, else keep generic columns."""
    if df_raw.empty:
        return df_raw
    first_row = df_raw.iloc[0]
    if all(isinstance(v, str) for v in first_row.tolist()):
        df = df_raw.iloc[1:].copy()
        df.columns = first_row.tolist()
    else:
        df = df_raw.copy()
        df.columns = [f"col_{i}" for i in range(len(df.columns))]
    df = df.dropna(how="all")
    df = df.reset_index(drop=True)
    return df


def _pick_date_col(df: pd.DataFrame) -> Optional[str]:
    best_col, best_score = None, 0
    for col in df.columns:
        parsed = _parse_dates(df[col])
        score = parsed.notna().sum()
        if score > best_score:
            best_col, best_score = col, score
    if best_score >= max(1, int(len(df) * 0.3)):
        return best_col
    return None


DATE_FORMATS = ["%d/%m/%Y", "%d/%m/%y", "%Y-%m-%d", "%d-%m-%Y", "%d.%m.%Y"]


def _parse_dates(series: pd.Series) -> pd.Series:
    """Parse date column without triggering format inference warnings.

    Tries a few common statement formats first, then falls back to a safe per-row parse.
    """
    if series is None or len(series) == 0:
        return pd.Series([], dtype="datetime64[ns]")

    text = series.astype(str).str.strip()
    text = text.replace({"": pd.NA, "nan": pd.NA})

    for fmt in DATE_FORMATS:
        parsed = pd.to_datetime(text, format=fmt, errors="coerce", dayfirst=True)
        if parsed.notna().sum() >= max(1, int(len(text) * 0.5)):
            return parsed

    def _safe_parse(val):
        if pd.isna(val):
            return pd.NaT
        try:
            return pd.to_datetime(val, errors="coerce", dayfirst=True)
        except Exception:
            try:
                return pd.Timestamp(datetime.strptime(str(val), "%d/%m/%Y"))
            except Exception:
                return pd.NaT

    return text.apply(_safe_parse)


def _numeric_ratio(series: pd.Series) -> float:
    numbers = series.apply(_clean_number)
    valid = numbers.notna().sum()
    return valid / len(series) if len(series) else 0.0


def _pick_amount_columns(df: pd.DataFrame) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """Return debit_col, credit_col, amount_col (only one of the three will be set)."""
    debit_col = None
    credit_col = None
    for col in df.columns:
        normalized = str(col).lower().replace("é", "e")
        if not debit_col and "debit" in normalized:
            debit_col = col
        if not credit_col and "credit" in normalized:
            credit_col = col

    amount_col = next((c for c in df.columns if "montant" in str(c).lower() or "amount" in str(c).lower()), None)

    if amount_col:
        return None, None, amount_col

    if debit_col or credit_col:
        return debit_col, credit_col, None

    # Fallback: pick the most numeric column as amount
    best_col, best_score = None, 0.0
    for col in df.columns:
        score = _numeric_ratio(df[col])
        if score > best_score:
            best_col, best_score = col, score
    if best_col and best_score >= 0.5:
        return None, None, best_col
    return None, None, None


def _pick_description_col(df: pd.DataFrame, used_cols: List[str]) -> Optional[str]:
    candidates = [c for c in df.columns if c not in used_cols]
    if not candidates:
        return None
    scored = []
    for col in candidates:
        series = df[col].fillna("").astype(str)
        avg_len = series.apply(len).mean()
        scored.append((avg_len, col))
    scored.sort(reverse=True)
    return scored[0][1] if scored else None


def _parse_text_lines(pdf) -> pd.DataFrame:
    """Fallback parser when tables are not detected: parse lines of text with two dates and an amount.

    Matches lines like:
    """
    line_pattern = re.compile(
        r"^(?P<date1>\d{2}/\d{2}/\d{4})\s+(?P<date2>\d{2}/\d{2}/\d{4})\s+(?P<desc>.+?)\s+(?P<amount>[+-]?\d[\d\s.,]*\d)$"
    )

    transactions = []
    current = None

    for page in pdf.pages:
        text = page.extract_text() or ""
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line:
                continue

            match = line_pattern.match(line)
            if match:
                op_date = pd.to_datetime(match.group("date1"), errors="coerce", dayfirst=True)
                amount = _clean_number(match.group("amount"))
                desc = match.group("desc").strip()

                if pd.isna(op_date) or amount is None:
                    current = None
                    continue

                current = {
                    "Date": op_date.strftime("%Y-%m-%d"),
                    "Description": desc,
                    "Montant": float(amount)
                }
                transactions.append(current)
            else:
                # Continuation line appended to previous description
                if current is not None:
                    current["Description"] = (current["Description"] + " " + line).strip()

    return pd.DataFrame(transactions)


def _detect_account_name(page_text: str) -> Tuple[Optional[str], Optional[str]]:
    """Detect account name and number. Returns (name, numero).

    Uses the account number as the primary differentiator between accounts.
    Handles patterns like: C/C EUROCOMPTE CONFORT N° 00094887301, LIVRET BLEU N° 123456789, etc.
    """
    if not page_text:
        return None, None

    # Try pattern: COMPTE_NAME N° NUMERO (works for C/C EUROCOMPTE, LIVRET BLEU, etc.)
    match = re.search(r"([A-Za-zÀ-ÖØ-öø-ÿ/\s]+?)\s+N°\s*(\d+)(?:\s+en\s+euros|$)", page_text, re.IGNORECASE)
    if match:
        compte_name = match.group(1).strip()
        numero = match.group(2)
        return compte_name, numero

    # Fallback: look for € followed by non-Date text
    match = re.search(r"€\s*\n\s*Date\s*\n\s*([^\n]+)", page_text)
    if match:
        return match.group(1).strip(), None

    # Last resort: € followed by text that's not a reserved word
    match = re.search(r"€\s*([A-Za-zÀ-ÖØ-öø-ÿ0-9 '\-_/]+?)(?:\s*\n|$)", page_text)
    if match:
        text = match.group(1).strip()
        if text.lower() not in ("date", ""):
            return text, None

    return None, None


def _detect_account_from_table(table) -> Tuple[Optional[str], Optional[str]]:
    """Try to detect account name/number inside the first rows of a table."""
    lines = []
    for row in table[:5]:
        if not row:
            continue
        line = " ".join(str(c) for c in row if c not in (None, ""))
        if line:
            lines.append(line)
    text = "\n".join(lines)
    if not text:
        return None, None

    match = re.search(r"([A-Za-zÀ-ÖØ-öø-ÿ/\s]+?)\s+N°\s*(\d+)(?:\s+en\s+euros|$)", text, re.IGNORECASE)
    if match:
        compte_name = match.group(1).strip()
        numero = match.group(2)
        return compte_name, numero
    return None, None


def parse_pdf_statement_by_account(uploaded_file) -> Tuple[Dict[str, pd.DataFrame], str]:
    """Parse PDF and return a mapping account_key -> DataFrame(Date, Description, Montant).
    
    Account key is based on numero first (unique identifier), then falls back to name.
    """
    try:
        account_rows: Dict[str, List[dict]] = {}
        account_metadata: Dict[str, str] = {}  # Track display names for keys
        
        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                compte_name_page, numero_page = _detect_account_name(page_text)
                
                # Page-level default account (used if table doesn't specify its own)
                if numero_page:
                    default_key = numero_page
                    default_display = f"{compte_name_page} ({numero_page})" if compte_name_page else f"Compte {numero_page}"
                elif compte_name_page:
                    default_key = compte_name_page
                    default_display = compte_name_page
                else:
                    default_key = "Inconnu"
                    default_display = "Inconnu"
                
                account_metadata[default_key] = account_metadata.get(default_key, default_display)

                # Find all € symbols in page to identify account sections
                page_lines = page_text.split('\n')
                context_lines = [line.strip() for line in page_lines if line.strip()]
                
                # Find all € occurrences to detect multiple accounts on same page
                euro_indices = []
                for i, line in enumerate(context_lines):
                    if '€' in line and line.strip() == '€':
                        euro_indices.append(i)
                
                tables = page.extract_tables() or []
                valid_table_count = 0  # Counter for valid tables only
                
                for table_idx, table in enumerate(tables, start=1):
                    # Filter: Skip tables with only 1 column (not real tables)
                    if not table or len(table[0]) < 3:
                        continue
                    
                    # Skip tables without € symbol (not account tables)
                    if not euro_indices:
                        continue
                    
                    # Increment valid table counter
                    valid_table_count += 1
                    
                    # For each valid table, find the corresponding € symbol
                    # Use valid_table_count (not table_idx) to match with euro_indices
                    euro_idx = euro_indices[min(valid_table_count - 1, len(euro_indices) - 1)]
                    
                    # Log table detection with title and preview
                    try:
                        table_info = f"[pdf_import] Table detected: page={page.page_number}, index={table_idx}, rows={len(table)}, cols={len(table[0]) if table else 0}"
                        print(table_info)
                        
                        # Special handling for page 3: show all lines
                        if page.page_number == 3:
                            print(f"  Toutes les lignes de la page 3:")
                            for ctx_line in context_lines:
                                if len(ctx_line) > 0:
                                    print(f"    {ctx_line[:120]}")
                        
                        print(f"  Lignes après € (compte #{valid_table_count}):")
                        for ctx_line in context_lines[euro_idx+1:euro_idx+4]:
                            if len(ctx_line) > 0:
                                print(f"    {ctx_line[:120]}")
                        
                        # Show table title (first row if it looks like a header)
                        if table and len(table) > 0:
                            first_row = table[0]
                            title = " | ".join([str(cell) for cell in first_row if cell not in (None, "")])
                            if title:
                                print(f"  Titre: {title}")
                        
                        # Show first few data rows
                        preview_rows = min(3, len(table))
                        if table and len(table) > 1:
                            print(f"  Aperçu des {preview_rows-1} premières lignes:")
                            for i in range(1, min(preview_rows+1, len(table))):
                                row_preview = " | ".join([str(cell)[:30] if cell else "" for cell in table[i] if cell not in (None, "")])
                                if row_preview:
                                    print(f"    {row_preview}")
                    except Exception as e:
                        print(f"[pdf_import] Table detected: page={page.page_number}, index={table_idx} (erreur affichage: {e})")
                    
                    # Detect account from lines after € symbol for this specific table
                    # Extract the relevant lines after the € that corresponds to this table
                    account_section_text = "\n".join(context_lines[euro_idx+1:euro_idx+4])
                    
                    # Try to detect account from the section text
                    compte_name_section, numero_section = _detect_account_name(account_section_text)
                    
                    # Also try table-based detection as fallback
                    compte_name_tbl, numero_tbl = _detect_account_from_table(table)
                    
                    # Prioritize section-based detection (from € lines), then table, then page-level
                    if numero_section:
                        account_key = numero_section
                        display_name = f"{compte_name_section} ({numero_section})" if compte_name_section else f"Compte {numero_section}"
                    elif numero_tbl:
                        account_key = numero_tbl
                        display_name = f"{compte_name_tbl} ({numero_tbl})" if compte_name_tbl else f"Compte {numero_tbl}"
                    elif compte_name_section:
                        account_key = compte_name_section
                        display_name = compte_name_section
                    elif compte_name_tbl:
                        account_key = compte_name_tbl
                        display_name = compte_name_tbl
                    else:
                        account_key = default_key
                        display_name = default_display

                    account_metadata[account_key] = account_metadata.get(account_key, display_name)
                    print(f"  → Compte attribué: {display_name}")

                    df_raw = pd.DataFrame(table)
                    df_raw = df_raw.dropna(how="all")
                    if df_raw.empty or df_raw.shape[1] < 2:
                        continue

                    df = _headerize(df_raw)
                    if df.empty:
                        continue

                    date_col = _pick_date_col(df)
                    debit_col, credit_col, amount_col = _pick_amount_columns(df)
                    desc_col = _pick_description_col(df, [date_col, debit_col, credit_col, amount_col])

                    if not date_col or not desc_col or (not amount_col and not debit_col and not credit_col):
                        continue

                    dates = _parse_dates(df[date_col])

                    if amount_col:
                        amounts = df[amount_col].apply(_clean_number)
                    else:
                        debit_vals = df[debit_col].apply(_clean_number) if debit_col else pd.Series([0] * len(df))
                        credit_vals = df[credit_col].apply(_clean_number) if credit_col else pd.Series([0] * len(df))
                        amounts = credit_vals.fillna(0) - debit_vals.fillna(0)

                    descriptions = df[desc_col].fillna("").astype(str)

                    for d, desc, amt in zip(dates, descriptions, amounts):
                        is_valid_amount = amt is not None
                        has_date = not pd.isna(d)
                        desc_txt = desc.strip()

                        if has_date and is_valid_amount:
                            account_rows.setdefault(account_key, []).append({
                                "Date": d.strftime("%Y-%m-%d"),
                                "Description": desc_txt,
                                "Montant": float(amt)
                            })
                        elif desc_txt and account_key in account_rows and account_rows[account_key]:
                            account_rows[account_key][-1]["Description"] = (account_rows[account_key][-1]["Description"] + " " + desc_txt).strip()

            if account_rows:
                # Sort keys by numero if present, then by display name
                sorted_keys = sorted(account_rows.keys(), key=lambda k: (k.isdigit() == False, k))
                result = {}
                for key in sorted_keys:
                    # Use display name as the returned key for UI
                    display_key = account_metadata.get(key, key)
                    result[display_key] = pd.DataFrame(account_rows[key])
                return result, ""

            # Fallback: try line-based parsing when no table returned
            print("[pdf_import] No structured tables kept; switching to line-based parsing")
            df_lines = _parse_text_lines(pdf)
            if not df_lines.empty:
                return {"Inconnu": df_lines}, ""

        return {}, "Aucun tableau exploitable n'a ete detecte."
    except Exception as exc:
        return {}, f"Erreur lors de la lecture du PDF: {exc}"


def parse_pdf_statement_flat(uploaded_file) -> Tuple[pd.DataFrame, str]:
    """Parse PDF and return a single DataFrame with a Compte column."""
    account_dfs, msg = parse_pdf_statement_by_account(uploaded_file)
    if not account_dfs:
        return pd.DataFrame(columns=["Date", "Description", "Montant", "Compte"]), msg
    frames = []
    for account_name, df in account_dfs.items():
        df2 = df.copy()
        df2["Compte"] = account_name
        frames.append(df2)
    merged = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=["Date", "Description", "Montant", "Compte"])
    return merged, ""


def parse_pdf_statement(uploaded_file) -> Tuple[pd.DataFrame, str]:
    """Backward-compatible parser returning all rows concatenated with Compte column."""
    return parse_pdf_statement_flat(uploaded_file)
