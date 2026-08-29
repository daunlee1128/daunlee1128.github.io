"""빌드 산출물에서 '외부 요청이 실제로 일어나는' 태그만 잡는 정규식.

test_jekyll_build(빌드된 HTML)와 test_structure(정규식 자체의 단위 검사)가 같이 쓴다.
jekyll-seo-tag 가 넣는 <link rel="canonical">·<link rel="alternate"> 는 브라우저가
요청을 보내지 않는 메타데이터이므로 외부 리소스가 아니다(오탐이었다).
"""
import re

EXTERNAL_SUBRESOURCE = re.compile(
    r'<(script|img|iframe|video|audio|source)[^>]*\ssrc="https?://'
    r'|<link[^>]*\srel="(stylesheet|preload|preconnect|prefetch|modulepreload|icon)"[^>]*\shref="https?://'
    r'|<link[^>]*\shref="https?://[^"]*"[^>]*\srel="(stylesheet|preload|preconnect|prefetch|modulepreload|icon)"',
    re.I)
