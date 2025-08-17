#!/bin/bash

echo "🚀 CMML Drug Analysis Dashboard Deployment"
echo "=========================================="

# Check if we're in the right directory
if [ ! -f "simple_dashboard.html" ]; then
    echo "❌ Error: simple_dashboard.html not found. Please run this script from the cmml_research directory."
    exit 1
fi

echo "✅ Found dashboard files"

# Create a simple index.html that redirects to the dashboard
cat > index.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CMML Drug Analysis Dashboard</title>
    <meta http-equiv="refresh" content="0; url=simple_dashboard.html">
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .loading {
            text-align: center;
        }
        .spinner {
            border: 4px solid rgba(255,255,255,0.3);
            border-radius: 50%;
            border-top: 4px solid white;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 20px auto;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="loading">
        <h1>CMML Drug Analysis Dashboard</h1>
        <div class="spinner"></div>
        <p>Loading dashboard...</p>
        <p><a href="simple_dashboard.html" style="color: white; text-decoration: underline;">Click here if not redirected automatically</a></p>
    </div>
</body>
</html>
EOF

echo "✅ Created index.html redirect"

# Create a .gitignore file
cat > .gitignore << 'EOF'
# Node modules
node_modules/

# Environment variables
.env
.env.local

# Logs
*.log

# OS generated files
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# IDE files
.vscode/
.idea/
*.swp
*.swo

# Temporary files
*.tmp
*.temp
EOF

echo "✅ Created .gitignore"

echo ""
echo "🎯 Deployment Options:"
echo "======================"
echo ""
echo "1. GitHub Pages (Free):"
echo "   - Create a GitHub repository"
echo "   - Push these files to the repository"
echo "   - Enable GitHub Pages in repository settings"
echo "   - Your dashboard will be available at: https://[username].github.io/[repo-name]"
echo ""
echo "2. Netlify (Free):"
echo "   - Go to https://netlify.com"
echo "   - Drag and drop this folder to deploy"
echo "   - Your dashboard will be available at a Netlify URL"
echo ""
echo "3. Vercel (Free):"
echo "   - Go to https://vercel.com"
echo "   - Import this folder as a project"
echo "   - Your dashboard will be available at a Vercel URL"
echo ""
echo "4. Local Development:"
echo "   - Run: python -m http.server 8080"
echo "   - Open: http://localhost:8080"
echo ""
echo "📁 Files ready for deployment:"
ls -la *.html *.json *.js *.css 2>/dev/null | head -10

echo ""
echo "✅ Ready for deployment!"
