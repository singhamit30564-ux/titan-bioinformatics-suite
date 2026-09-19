"""Small I/O helpers for common export patterns."""
from __future__ import annotations

import io
import pandas as pd


def df_to_csv_bytes(df: pd.DataFrame) -> bytes:
    """Encode a DataFrame as UTF-8 CSV bytes suitable for st.download_button."""
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    return buf.getvalue().encode("utf-8")


def safe_csv_download(label: str, df: pd.DataFrame, filename: str,
                      key: str | None = None) -> None:
    """Render a working CSV download button for a DataFrame."""
    st_obj = __import__("streamlit")
    st_obj.download_button(
        label,
        data=df_to_csv_bytes(df),
        file_name=filename,
        mime="text/csv",
        use_container_width=True,
        key=key,
    )


def safe_fasta_download(label: str, sequences: dict[str, str], filename: str,
                        key: str | None = None) -> None:
    """Render a FASTA download button. `sequences` maps header→sequence."""
    st_obj = __import__("streamlit")
    lines = []
    for header, seq in sequences.items():
        lines.append(f">{header}")
        # Wrap at 70 chars (FASTA convention)
        for i in range(0, len(seq), 70):
            lines.append(seq[i:i + 70])
    fasta_str = "\n".join(lines) + "\n"
    st_obj.download_button(
        label,
        data=fasta_str.encode("utf-8"),
        file_name=filename,
        mime="text/plain",
        use_container_width=True,
        key=key,
    )
