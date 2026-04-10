print('Hello, World!')
print('Testing PyInstaller...')
try:
    import xml.parsers.expat
    print('Successfully imported xml.parsers.expat')
except Exception as e:
    print(f'Error importing xml.parsers.expat: {e}')
input('Press Enter to exit...')
