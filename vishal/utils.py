def markdown_to_whatsapp(text):
    # Replace bold **text** → *text*
    text = re.sub(r"\*\*(.*?)\*\*", r"*\1*", text)

    # Replace italic *text* → _text_
    text = re.sub(r"(?<!\*)\*(.*?)\*(?!\*)", r"_\1_", text)

    # Replace strikethrough ~~text~~ → ~text~
    text = re.sub(r"~~(.*?)~~", r"~\1~", text)

    # Replace inline code `code` → ```code``` (monospace)
    text = re.sub(r"`(.*?)`", r"```\1```", text)

    # Replace links [title](url) → title (url)
    text = re.sub(r"\[(.*?)\]\((.*?)\)", lambda m: f"{m.group(1)} ({shorten_url(m.group(2))})", text)

    # Replace images ![alt](url) → [alt]
    text = re.sub(r"!\[(.*?)\]\((.*?)\)", lambda m: f"[{m.group(1) or 'Screenshot'}]", text)

    return text
