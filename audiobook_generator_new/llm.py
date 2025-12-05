import os, textwrap, time

OPENAI_KEY = os.environ.get('OPENAI_API_KEY')
USE_OPENAI = bool(OPENAI_KEY)

def enrich_text_for_audiobook(text, use_openai=False):
    """Main entrypoint. If use_openai True and OPENAI_API_KEY is present, will call OpenAI API.
    Otherwise uses a local heuristic-based rewriter to make text more 'audiobook-friendly'.
    """

    if use_openai and USE_OPENAI:
        try:
            import openai
            openai.api_key = OPENAI_KEY
            prompt = f"Rewrite the following text for an engaging audiobook narration. Keep natural pacing, add short connective phrases where helpful, and keep paragraphs suitable for spoken word:\n\n{text[:15000]}"
            resp = openai.ChatCompletion.create(
                model='gpt-4o-mini',
                messages=[{'role':'user','content':prompt}],
                max_tokens=2048,
                temperature=0.8
            )
            out = resp['choices'][0]['message']['content']
            return out
        except Exception as e:
            # fallback
            print('OpenAI error, falling back to local rewrite:', e)
    # Local heuristic fallback rewriter
    return local_rewrite_for_audiobook(text)

def local_rewrite_for_audiobook(text):
    """A simple, deterministic transformation to make text slightly more 'spoken'.
    This is a fallback so the app works without an API key. It performs:
    - Sentence splitting by punctuation, re-joins with slight connective phrases
    - Shortens very long paragraphs
    - Adds simple narration cues
    """
    import re
    # Normalize whitespace
    t = re.sub(r'\s+', ' ', text).strip()
    # Split into sentences naively
    sentences = re.split(r'(?<=[\.\?\!])\s+', t)
    out_sents = []
    for i, s in enumerate(sentences):
        s = s.strip()
        if not s:
            continue
        # Add a small narration connective occasionally
        if i % 7 == 0 and i != 0:
            out_sents.append('\n\n[Pause for effect]\n')
        # Ensure sentences are not extremely long: break them
        if len(s) > 300:
            # break into shorter chunks
            chunks = [s[i:i+200].rsplit(' ',1)[0] for i in range(0, len(s), 200)]
            out_sents.extend(chunks)
        else:
            out_sents.append(s)
    # Join with newline paragraphs every 6 sentences
    paragraphs = []
    for i in range(0, len(out_sents), 6):
        para = ' '.join(out_sents[i:i+6])
        paragraphs.append(para)
    # Add final narration header
    header = "Narrator: This audiobook is automatically generated. The following content has been adapted for spoken narration."\
             if len(paragraphs) > 0 else ''
    return header + '\n\n' + '\n\n'.join(paragraphs)
