# Move the main modules into src/ifw/
mv use_azure src/ifw/
mv use_gcp src/ifw/
mv use_docker src/ifw/
mv model.py src/ifw/

# Clean up cache files (optional but recommended)
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true