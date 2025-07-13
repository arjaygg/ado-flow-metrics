# Troubleshooting Guide - Flow Metrics Dashboard

## 🔧 Common Issues and Solutions

### ❌ Error: `{"detail":"Not Found"}`

This error typically occurs when trying to access resources that aren't available. Here are the solutions:

#### **Quick Fix - Use the Testing Server**
```bash
# Method 1: Use the provided testing script
python3 start_testing.py

# Method 2: Use Python's built-in server
python3 -m http.server 8090
# Then visit: http://localhost:8090/dashboard.html
```

#### **Root Causes and Solutions**

1. **Missing Dependencies (CLI Commands)**
   ```bash
   # Install required dependencies
   pip install -r requirements.txt
   
   # Or install minimal requirements for testing
   pip install click rich flask
   ```

2. **Wrong File Paths**
   ```bash
   # Ensure you're in the project directory
   cd /home/devag/git/feat-ado-flow
   
   # Verify files exist
   ls -la dashboard.html executive-dashboard.html
   ls -la js/workstream*.js
   ```

3. **Port Already in Use**
   ```bash
   # Kill existing servers
   pkill -f "http.server"
   pkill -f "python3 -c"
   
   # Try different port
   python3 -m http.server 8091
   ```

4. **Missing JavaScript Files**
   ```bash
   # Check if js/ directory exists
   ls -la js/
   
   # Should contain:
   # - workstream_config.js
   # - workstream-manager.js
   ```

### ❌ Error: `ModuleNotFoundError: No module named 'click'`

**Solution:**
```bash
# Install CLI dependencies
pip install click rich flask pandas

# Or install all dependencies
pip install -r requirements.txt
```

### ❌ Error: JavaScript files not loading

**Symptoms:** Dropdowns don't populate, charts don't render
**Solution:**
```bash
# Verify files are in correct location
ls -la js/workstream_config.js js/workstream-manager.js

# Check browser console for 404 errors
# Open browser dev tools (F12) and check Console tab
```

### ❌ Error: `OSError: [Errno 98] Address already in use`

**Solution:**
```bash
# Find and kill processes using the port
lsof -ti:8080 | xargs kill -9

# Or use a different port
python3 -m http.server 8091
```

## ✅ Recommended Testing Setup

### **Option 1: Simple Testing (Recommended)**
```bash
# Navigate to project directory
cd /home/devag/git/feat-ado-flow

# Start testing server
python3 start_testing.py

# Open URLs in browser:
# http://localhost:8090/dashboard.html
# http://localhost:8090/executive-dashboard.html
```

### **Option 2: Python HTTP Server**
```bash
# Navigate to project directory
cd /home/devag/git/feat-ado-flow

# Start server
python3 -m http.server 8090

# Open in browser:
# http://localhost:8090/dashboard.html
```

### **Option 3: CLI Server (Requires Dependencies)**
```bash
# Install dependencies first
pip install -r requirements.txt

# Then use CLI
python3 -m src.cli serve --port 8000 --open-browser
```

## 🧪 Testing Checklist

### Before Testing:
- [ ] In correct directory: `/home/devag/git/feat-ado-flow`
- [ ] HTML files exist: `dashboard.html`, `executive-dashboard.html`
- [ ] JS files exist: `js/workstream_config.js`, `js/workstream-manager.js`
- [ ] Server running on available port

### During Testing:
- [ ] Main dashboard loads without errors
- [ ] Executive dashboard loads without errors
- [ ] Work Item Type dropdown populates
- [ ] Sprint dropdown populates
- [ ] Filters work and update charts
- [ ] Defect ratio chart displays and configures

### Browser Console Check:
1. Open browser developer tools (F12)
2. Check Console tab for errors
3. Check Network tab for failed requests
4. Look for 404 errors on JavaScript files

## 🔍 Debug Information

### Check File Structure:
```bash
tree -L 2 /home/devag/git/feat-ado-flow/
# Should show:
# ├── dashboard.html
# ├── executive-dashboard.html
# ├── js/
# │   ├── workstream_config.js
# │   └── workstream-manager.js
# └── src/
```

### Test Network Connectivity:
```bash
# Test if server is responding
curl -I http://localhost:8090/dashboard.html

# Test if JS files are accessible
curl -I http://localhost:8090/js/workstream_config.js
```

### Validate Test Suite:
```bash
# Run comprehensive tests
python3 test_new_features.py

# Should show: 4/4 tests passed (100% success rate)
```

## 📞 Getting Help

If you continue experiencing issues:

1. **Check browser console** for specific error messages
2. **Verify file permissions** with `ls -la`
3. **Test with different browsers** (Chrome, Firefox, Safari)
4. **Try different ports** if address conflicts occur
5. **Run the test suite** to verify functionality

## 🚀 Quick Recovery Commands

```bash
# Full reset and restart
cd /home/devag/git/feat-ado-flow
pkill -f "python3"
sleep 2
python3 start_testing.py
```

This should resolve most common issues and get you testing the new features immediately!