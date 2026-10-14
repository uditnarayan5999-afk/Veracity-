import re
import requests
import urllib.parse
from bs4 import BeautifulSoup

def calculate_similarity(text1, text2):
    if not text1 or not text2:
        return 0.0
    try:
        words1 = [w.strip('.,()!?"\'{}[]++;').lower() for w in text1.split() if w.strip('.,()!?"\'{}[]++;')]
        words2 = [w.strip('.,()!?"\'{}[]++;').lower() for w in text2.split() if w.strip('.,()!?"\'{}[]++;')]
        if not words1:
            return 0.0
            
        set_words2 = set(words2)
        overlap = sum(1 for w in words1 if w in set_words2)
        score = overlap / len(words1)
        return float(score)
    except Exception as e:
        print(f"Similarity error: {e}")
        return 0.0

def search_duckduckgo(query):
    try:
        url = "https://html.duckduckgo.com/html/"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        }
        data = {'q': query}
        response = requests.post(url, headers=headers, data=data, timeout=8)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            results = []
            for div in soup.find_all('div', class_='result')[:5]:
                title_elem = div.find('a', class_='result__a')
                snippet_elem = div.find('a', class_='result__snippet') or div.find('div', class_='result__snippet')
                
                if not title_elem or not snippet_elem:
                    continue

                raw_href = title_elem.get('href', '')
                actual_url = raw_href
                
                # Robust DuckDuckGo 'uddg' Destination Decoding
                if 'uddg=' in raw_href:
                    try:
                        # Extract everything after uddg= up to the next &
                        pos = raw_href.find('uddg=') + 5
                        end = raw_href.find('&', pos)
                        if end == -1:
                            encoded_url = raw_href[pos:]
                        else:
                            encoded_url = raw_href[pos:end]
                        actual_url = urllib.parse.unquote(encoded_url)
                    except:
                        pass
                elif raw_href.startswith('//'):
                    actual_url = 'https:' + raw_href
                        
                results.append({
                    'body': snippet_elem.get_text().strip(),
                    'href': actual_url
                })
            return results
    except Exception as e:
        print(f"Backend Search Error: {e}")
    return []

def calculate_synthetic_score(text, is_code):
    score = 5.0 # Base minimum
    
    # Common synthetic vocabulary and structures
    synthetic_phrases = [
        'furthermore', 'moreover', 'delve', 'tapestry', 'testament', 
        'in conclusion', 'ultimately', 'vital', 'crucial', 'multifaceted',
        'as an ai', 'language model', "let's break down", 'certainly', 
        'here is', 'it is important to note', 'however,'
    ]
                
    text_lower = text.lower()
    for word in synthetic_phrases:
        if word in text_lower:
            score += 15.0
            
    # Grammar/Formatting heuristics indicating structured generation
    if text.count(':') > 2 and text.count('- ') > 2:
        score += 20.0
        
    if is_code:
        # Heavily standard synthetic code structure
        if "//" in text and ("check if" in text_lower or "return " in text_lower or "initialize" in text_lower):
            score += 35.0
        if "printf(" in text or "console.log" in text or "print(" in text:
            score += 10.0
        if "```" in text:
            score += 40.0
            
    return round(min(max(score, 0.0), 99.0), 1)

def check_plagiarism(text):
    is_code = ('{' in text and ';' in text) or ('#include' in text) or ('def ' in text)
    
    if is_code:
        raw_chunks = re.split(r'[;\n]', text)
        sentences = [s.strip() for s in raw_chunks if len(s.strip().split()) > 3]
    else:
        sentences = re.split(r'(?<=[.!?]) +', text.replace('\n', ' '))
        sentences = [s.strip() for s in sentences if len(s.split()) > 3]
        
    sentences = sentences[:15]
    total_sentences = len(sentences)
    plagiarized_sentences_count = 0
    detailed_results = []
    
    for sentence in sentences:
        best_match_score = 0.0
        best_match_url = None
        best_match_snippet = None
        
        try:
            clean_sentence = re.sub(r'[^\w\s]', '', sentence)
            query_words = clean_sentence.split()
            if len(query_words) > 5:
                query = " ".join(query_words[:6])
            else:
                query = clean_sentence
                
            search_results = search_duckduckgo(f'"{query}"')
            if not search_results:
                search_results = search_duckduckgo(query)
            
            for res in search_results:
                snippet = res.get('body', '')
                url = res.get('href', '')
                
                if snippet:
                    sim_score = calculate_similarity(sentence, snippet)
                    if sim_score > best_match_score:
                        best_match_score = sim_score
                        best_match_url = url
                        best_match_snippet = snippet
        except Exception as e:
            print(f"Search failed for chunk: {e}")
            
        threshold = 0.50 if is_code else 0.30 # Slightly lower thresholds for better sensitivity
        is_plagiarized = best_match_score >= threshold
        if is_plagiarized:
            plagiarized_sentences_count += 1
            
        detailed_results.append({
            "sentence": sentence,
            "is_plagiarized": bool(is_plagiarized),
            "similarity_score": round(float(best_match_score), 2),
            "matched_url": best_match_url,
            "matched_snippet": best_match_snippet
        })
        
    overall_score = (plagiarized_sentences_count / total_sentences) if total_sentences > 0 else 0.0
    
    # Run the advanced synthetic heuristic
    synthetic_prob = calculate_synthetic_score(text, is_code)
    
    return {
        "overall_score": round(overall_score, 2),
        "total_analyzed_sentences": total_sentences,
        "plagiarized_sentences_count": plagiarized_sentences_count,
        "is_code_detected": is_code,
        "ai_probability": synthetic_prob,
        "details": detailed_results
    }
