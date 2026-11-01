# Sean Yeon — CPA Data Scientist 블로그

Wix에서 옮겨온 나만의 블로그입니다. 글은 Markdown 파일, 사이트는 `build.py`가 만들고, GitHub Pages가 무료로 호스팅합니다.

## 폴더 구조

```
content/posts/   ← 블로그 글 (글 1편 = .md 파일 1개, 현재 47편)
content/about.md ← About 페이지
static/images/   ← 이미지 (Wix에서 가져온 56장 포함)
site.yml         ← 사이트 이름, 소개, 주소(url) 등 설정
build.py         ← 사이트 생성기
setup/github-pages-deploy.yml ← 자동 빌드·배포 설정 (.github/workflows 로 옮겨 사용)
```

## 새 글 쓰기

1. `content/posts/` 에 새 파일을 만듭니다. 파일 이름이 주소가 됩니다.
   예) `my-first-post.md` → `https://cpasean.github.io/BLOG/post/my-first-post/`
2. 맨 위에 아래 머리말을 넣고, 그 아래에 본문을 Markdown으로 씁니다.

~~~markdown
---
title: "Monte Carlo simulation for retirement savings"
date: 2026-11-02
category: Work        # Work 또는 Life
---

본문을 여기에 씁니다. **굵게**, *기울임*, [링크](https://example.com)

![차트 설명](/images/my-chart.png)

```python
import numpy as np
returns = np.random.normal(0.07, 0.15, 10_000)
```

수식도 됩니다: $$P(A|B) = \frac{P(B|A)P(A)}{P(B)}$$
~~~

- 이미지는 `static/images/` 에 넣고 `/images/파일이름` 으로 씁니다.
- 아직 공개하지 않을 글은 머리말에 `draft: true` 를 넣으면 빌드에서 빠집니다.
- Jupyter 노트북을 글로 올리려면: `jupyter nbconvert --to markdown 노트북.ipynb` 로 변환한 뒤, 머리말을 붙여 `content/posts/` 에 넣고 생성된 그림 파일은 `static/images/` 로 옮기세요.

## 내 컴퓨터에서 미리 보기

```bash
pip install -r requirements.txt
python build.py
python -m http.server 8000 --directory dist
```
브라우저에서 http://localhost:8000 을 엽니다.

## 배포 (GitHub Pages, 무료)

- 저장소: https://github.com/cpasean/BLOG
- 블로그 주소: https://cpasean.github.io/BLOG/
- 저장소의 `main` 브랜치에 글을 올리면(push) `.github/workflows/deploy.yml`이 자동으로 빌드해서 1~2분 뒤 사이트에 반영됩니다.
- 가장 쉬운 방법: GitHub 웹에서 `content/posts` 폴더 → **Add file → Create new file** 로 글을 바로 써도 됩니다.
- 내 컴퓨터에서 쓰려면 GitHub Desktop으로 저장소를 내려받아(clone) 그 폴더에서 작업하세요.
- 주소를 `cpasean.github.io` 로 짧게 하려면: 저장소 이름을 `cpasean.github.io` 로 바꾸고 `site.yml`의 `url`을 `https://cpasean.github.io` 로 고치면 됩니다.
- `setup/github-pages-deploy.yml` 은 `.github/workflows/deploy.yml` 의 사본입니다.

## 나중에 도메인을 사면

1. 도메인 구입 (예: seanyeon.com, 연 $10~15 정도)
2. `site.yml` 의 `url` 을 새 도메인으로 변경
3. GitHub 저장소 **Settings → Pages → Custom domain** 에 도메인 입력, 도메인 업체 DNS에 GitHub 안내대로 레코드 추가

## 이전 메모 (Wix → 새 사이트)

- 글 주소 형식 `/post/글-이름` 을 그대로 유지했습니다.
- 카테고리가 없던 글 8편은 `Life` 로 분류했습니다. 바꾸려면 각 파일의 `category:` 를 고치세요.
- 세션 값이 들어 있어 더는 작동하지 않는 링크 2개를 정리했습니다:
  IRS 온라인 신원 확인(→ irs.gov 공식 안내 페이지), Form 8822 링크(→ form-8822.com 첫 페이지).
- Wix 무료 주소에서는 자동 이동(리디렉션)을 걸 수 없으니, Wix 홈에 새 주소 안내 글을 남겨 두세요.
