# VRP Backend

## GitHub'a Push Etme

1. GitHub'da yeni repository oluştur
2. Aşağıdaki komutları çalıştır:

```bash
git remote add origin https://github.com/USERNAME/REPO_NAME.git
git branch -M main
git push -u origin main
```

## Netlify'da Deploy

1. Netlify'da "New site from Git" seç
2. GitHub repository'yi bağla
3. Build settings:
   - Build command: `echo "No build required"`
   - Publish directory: `.`
4. Environment variables ekle:
   - `GEMINI_API_KEY`
   - `GOOGLE_MAPS_API_KEY`

## API Endpoints

- `/api/vrp/solve` - VRP çözümü
- `/api/directions` - Directions API
