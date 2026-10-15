from app.backend.product_analyzer.description_generator import DescriptionGenerator



generator = DescriptionGenerator()

print("*** GENERANDO NUEVA DESCRIPCIÓN ***")
nombre_empresa = "AlolaIA"
old_description = """
Calvin Klein CK IN2U es un Eau de Toilette floral y cítrico para mujeres que están conectadas con lo que quieren en cualquier lugar y en cualquier momento. El chispeante pomelo y la irresistible orquídea de azúcar encabezan esta seductora fragancia, envueltos en la calidez del ámbar neón y el soufflé de vainilla. Una fragancia con una estela persistente que resulta perfecta para cualquier ocasión.
"""
visual_metadata = ['perfume', 'black']
keywords = ['Gran olor', 'duración óptima', 'recomedable', 'frasco bonito']

print(generator.generate_new_product_description(nombre_empresa, old_description, visual_metadata, keywords, 'Profesional y cercano'))
