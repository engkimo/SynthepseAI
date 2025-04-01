import sys
sys.path.append('.')

try:
    from core.rome_model_editor import ROMEModelEditor
    print('ROME import successful')
except Exception as e:
    print(f'ROME import failed: {str(e)}')

try:
    from core.coat_reasoner import COATReasoner
    print('COAT import successful')
except Exception as e:
    print(f'COAT import failed: {str(e)}')

try:
    from core.rgcn_processor import RGCNProcessor
    print('RGCN import successful')
except Exception as e:
    print(f'RGCN import failed: {str(e)}')
