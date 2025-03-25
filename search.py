from annoy import AnnoyIndex
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import pickle
import textdistance
from sklearn.feature_extraction.text import TfidfVectorizer

def diagnosticar_embeddings():
    """
    Diagnostica los embeddings cargados desde un archivo pickle.
    
    Retorna:
    int: Dimensión de los embeddings o None si no se encontraron embeddings válidos
    """
    file_path = 'embeddings/embeddings_d.pkl'
    try:
        # Cargar los embeddings desde el archivo pickle
        print("Cargando embeddings desde archivo pickle...")
        with open(file_path, 'rb') as f:
            embeddings_list = pickle.load(f)
        
        print(f"Total de embeddings en el archivo: {len(embeddings_list)}")
        
        # Verificar el tipo de datos del primer embedding
        if len(embeddings_list) > 0:
            print(f"Tipo de datos del primer embedding: {type(embeddings_list[0])}")
        else:
            print("El archivo no contiene embeddings")
            return None
        
        # Encontrar un embedding válido y su dimensión
        for idx, embedding in enumerate(embeddings_list):
            try:
                # Si es un numpy array, ya tenemos lo que necesitamos
                if isinstance(embedding, np.ndarray):
                    dimension = embedding.shape[0]
                    print(f"\nEncontrado embedding válido en posición {idx}")
                    print(f"Dimensión: {dimension}")
                    print(f"Primeros 5 valores: {embedding[:5]}")
                    return dimension
                
                # Si es una lista, convertirla a numpy array
                elif isinstance(embedding, list):
                    embedding_array = np.array(embedding)
                    dimension = len(embedding_array)
                    print(f"\nEncontrado embedding válido en posición {idx}")
                    print(f"Dimensión: {dimension}")
                    print(f"Primeros 5 valores: {embedding[:5]}")
                    return dimension
                
                # Si es otro tipo, intentar convertirlo
                else:
                    print(f"Embedding en posición {idx} no es un array o lista, es {type(embedding)}")
                    continue
                    
            except Exception as e:
                print(f"Error al procesar embedding en posición {idx}: {e}")
                continue
        
        print("\nNo se encontró ningún embedding válido.")
        print("Verifica el formato de los embeddings en el archivo pickle.")
        return None
        
    except FileNotFoundError:
        print(f"No se encontró el archivo {file_path}. Verifica la ruta.")
        return None
    except Exception as e:
        print(f"Error al cargar los embeddings: {e}")
        return None

def crear_indice_annoy_con_dimension(df, dimension):
    """
    Crea un índice Annoy cargando los embeddings desde un archivo pickle.
    
    Parámetros:
    df (pandas.DataFrame): DataFrame con los datos
    dimension (int): Dimensión de los embeddings
    
    Retorna:
    tuple: (index, indices_validos) - El índice Annoy y el mapeo de índices
    """

    file_path = 'embeddings/embeddings_d.pkl'
    # Crear índice Annoy
    index = AnnoyIndex(dimension, 'angular')
    
    # Mapeo entre índices de Annoy y DataFrame
    indices_validos = {}
    count = 0
    
    try:
        # Cargar los embeddings desde el archivo pickle
        print("Cargando embeddings desde archivo pickle...")
        with open(file_path, 'rb') as f:
            embeddings_list = pickle.load(f)
        
        print(f"Se cargaron {len(embeddings_list)} embeddings desde el archivo")
        
        # Verificar que la cantidad de embeddings coincida con el DataFrame
        if len(embeddings_list) != len(df):
            print(f"ADVERTENCIA: El número de embeddings ({len(embeddings_list)}) no coincide con el número de filas en el DataFrame ({len(df)})")
        
        # Agregar items al índice
        for df_idx, embedding in enumerate(embeddings_list):
            try:
                # Verificar que el embedding sea un array de numpy
                if isinstance(embedding, np.ndarray):
                    # Verificar dimensión
                    if len(embedding) == dimension:
                        index.add_item(count, embedding)
                        indices_validos[count] = df_idx
                        count += 1
                        
                        # Imprimir progreso cada 1000 items
                        if count % 1000 == 0:
                            print(f"Procesados {count} embeddings")
                    else:
                        print(f"Advertencia: El embedding en posición {df_idx} tiene dimensión {len(embedding)}, se esperaba {dimension}")
                else:
                    # Intentar convertir a numpy array si no es un array
                    try:
                        embedding_array = np.array(embedding)
                        if len(embedding_array) == dimension:
                            index.add_item(count, embedding_array)
                            indices_validos[count] = df_idx
                            count += 1
                    except:
                        print(f"No se pudo convertir el embedding en posición {df_idx} a un array")
            except Exception as e:
                print(f"Error al procesar embedding en posición {df_idx}: {e}")
                continue
        
        print(f"Total de embeddings añadidos al índice: {count}")
        
        # Construir el índice (10 árboles por defecto)
        print("Construyendo índice Annoy...")
        index.build(10)
        print("Índice construido exitosamente")
        
        return index, indices_validos
    
    except FileNotFoundError:
        print(f"No se encontró el archivo {file_path}. Verificar la ruta.")
        raise
    except Exception as e:
        print(f"Error al cargar los embeddings: {e}")
        raise

def load_model(model_name):
    # Cargar modelo
    print("Cargando modelo de embeddings...")
    model = SentenceTransformer(model_name)
    return model


def extract_consonants(text):
    """
    Extrae solo las consonantes de un string, eliminando vocales y otros caracteres.
    
    Args:
        text (str): El texto del cual extraer las consonantes
        
    Returns:
        str: El texto con solo las consonantes en minúsculas
    """
    if not isinstance(text, str):
        return ""
    
    vowels = "aeiouáéíóúàèìòùäëïöüâêîôûAEIOUÁÉÍÓÚÀÈÌÒÙÄËÏÖÜÂÊÎÔÛ"
    return ''.join(c.lower() for c in text if c.isalpha() and c.lower() not in vowels)

def get_consonant_words(text):
    """
    Convierte un texto en una lista de palabras con solo consonantes.
    
    Args:
        text (str): El texto a procesar
        
    Returns:
        list: Lista de palabras con solo consonantes
    """
    words = text.split()
    return [extract_consonants(word) for word in words if extract_consonants(word)]

def longest_common_subsequence(s1, s2):
    """
    Encuentra la subsecuencia común más larga entre dos strings.
    Mantiene el orden de los caracteres.
    
    Args:
        s1 (str): Primer string
        s2 (str): Segundo string
        
    Returns:
        int: Longitud de la subsecuencia común más larga
    """
    m, n = len(s1), len(s2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s1[i-1] == s2[j-1]:
                dp[i][j] = dp[i-1][j-1] + 1
            else:
                dp[i][j] = max(dp[i-1][j], dp[i][j-1])
                
    return dp[m][n]

def calculate_match_percentage(word, compare_words):
    """
    Calcula el porcentaje máximo de coincidencia entre una palabra
    y una lista de palabras, respetando el orden de los caracteres.
    
    Args:
        word (str): Palabra a comparar (solo consonantes)
        compare_words (list): Lista de palabras para comparar (solo consonantes)
        
    Returns:
        tuple: (porcentaje máximo de coincidencia, palabra con la que coincide mejor)
    """
    if not word or not compare_words:
        return 0, ""
    
    max_percentage = 0
    best_match = ""
    
    for comp_word in compare_words:
        if not comp_word:
            continue
            
        lcs_length = longest_common_subsequence(word, comp_word)
        
        # Si palabra original es más corta que la comparada, usamos su longitud como base
        # Si palabra original es más larga, también usamos su longitud como base
        # Esto penaliza tanto palabras faltantes como palabras adicionales
        percentage = (lcs_length / len(word)) * 100
        
        if percentage > max_percentage:
            max_percentage = percentage
            best_match = comp_word
    
    return max_percentage, best_match

def compare_consonant_matches(original_text, compare_text):
    """
    Compara dos textos eliminando vocales y calculando el porcentaje
    máximo de coincidencia para cada palabra del texto original.
    
    Args:
        original_text (str): Texto original a analizar
        compare_text (str): Texto con el que comparar
        
    Returns:
        dict: Diccionario con palabras originales y sus mejores coincidencias
    """
    # Extraer palabras con solo consonantes
    original_words = get_consonant_words(original_text)
    compare_words = get_consonant_words(compare_text)
    
    # Mapear palabras originales a sus versiones con solo consonantes
    word_mapping = {}
    for word in original_text.split():
        cons_word = extract_consonants(word)
        if cons_word:  # Solo incluir palabras que tengan consonantes
            word_mapping[cons_word] = word
    
    results = {}
    
    # Para cada palabra consonante del texto original
    for cons_word in original_words:
        # Calcular el % máximo de coincidencia
        max_percentage, best_match = calculate_match_percentage(cons_word, compare_words)
        
        # Recuperar la palabra original
        original_word = word_mapping.get(cons_word, cons_word)
        
        # Guardar resultados
        results[original_word] = {
            "consonants": cons_word,
            "match_percentage": round(max_percentage, 2),
            "best_match": best_match
        }
    
    return results

def singular(palabra):
    terminaciones = ["as", "os", "es"]
    for terminacion in terminaciones:
        if palabra.endswith(terminacion):
            return palabra[:-len(terminacion)]
    return palabra

def key_search(nsearch, options, df, considerar_ofertas):
    
    search_bool = True


    if options[f'search_{0}'] == '':
        return False
    df['search_text'] = df['search_text'].fillna('')
    if options[f'contains_{0}'] == 'Contiene':
        search_bool = (df['search_text'].str.lower().str.contains(options[f'search_{0}'].lower()))
    else:
        search_bool = ~(df['search_text'].str.lower().str.contains(options[f'search_{0}'].lower()))

    for i in range(1, nsearch):
        if options[f'search_{i}'] != '':
          if options[f'logical_{i}'] == 'Y':
              if options[f'contains_{i}'] == 'Contiene':                
                  search_bool = search_bool & (df['search_text'].str.lower().str.contains(options[f'search_{i}'][:-1].lower()))
              else:
                  search_bool = search_bool & (~(df['search_text'].str.lower().str.contains(options[f'search_{i}'][:-1].lower())))
          elif options[f'logical_{i}'] == 'O':
              if options[f'contains_{i}'] == 'Contiene':
                  search_bool = search_bool | (df['search_text'].str.lower().str.contains(options[f'search_{i}'][:-1].lower()))
              else:
                  search_bool = search_bool | (~(df['search_text'].str.lower().str.contains(options[f'search_{i}'][:-1].lower())))

        else:
            break
    

    df = df[search_bool].drop(columns=['search_text'])

    if considerar_ofertas:
        # Agregar una columna auxiliar con el menor valor entre A y B
        df['Min_Val'] = df[['Precio MSM', 'Precio Oferta']].min(axis=1)

        # Ordenar según la nueva columna
        df = df.sort_values(by='Min_Val', ascending=True)

        # Eliminar la columna auxiliar si no se necesita
        df = df.drop(columns=['Min_Val'])
    else:
        df = df.sort_values(by=df['Precio MSM'], ascending=True)
    return df


def do_search(search_term, model, vectorizer, index, indices_validos, df, embeddings, options, top_n=500, show=200):
    orden = options[0]
    considerar_ofertas = options[1]


    # Generar embedding para la consulta
    query_embedding = model.encode(search_term)
    annoy_indices, distances = index.get_nns_by_vector(query_embedding, top_n, include_distances=True)
    
    query_tfidf = vectorizer.transform([search_term])

    # Convertir distancias a similitudes
    similitudes = [1 - (d**2)/2 for d in distances]

    has_prov = False
    # Caso en que se busca un proveedor en la query
    proveedores = df['Proveedor'].unique()
    for prov in proveedores:
        if prov.lower() in search_term.lower():
            has_prov = True
            if len(search_term.split()) == 1:
                df_prov = df[(df['Proveedor'] == prov) | (df['Descripcion'].str.lower().str.contains(prov.lower()))]
                prov_results = {idx: None for idx in df_prov.index}
                return list(prov_results.items())[:top_n]
            else:
                df = df[(df['Proveedor'] == prov) | (df['Descripcion'].str.lower().str.contains(prov.lower()))]
    
    df = df[(df['Descripcion'].str.lower().str.contains(singular(search_term.lower().split()[0]))) | (df['Info Producto'].str.lower().str.contains(singular(search_term.lower().split()[0])))]
    
    results = {}
    for i, annoy_idx in enumerate(annoy_indices):
        if annoy_idx in indices_validos:
            df_idx = indices_validos[annoy_idx]
            try:
              precio_msm = df.loc[df_idx, :].get('Precio MSM', 0)
              precio_oferta = df.loc[df_idx, :].get('Precio Oferta', 0)
              descripcion = df.loc[df_idx, :].get('Descripcion', "")
              search_text = df.loc[df_idx, :].get('search_text', "")
              proveedor = df.loc[df_idx, :].get('Proveedor', "")
            except:
                continue
            embedding_allinfo = embeddings[0][df_idx]
            embedding_descripcion = embeddings[1][df_idx]
            embedding_tfidf = embeddings[2][df_idx]
            similarity_allinfo = cosine_similarity(query_embedding.reshape(1, -1), embedding_allinfo.reshape(1, -1))[0][0]
            similarity_descripcion = cosine_similarity(query_embedding.reshape(1, -1), embedding_descripcion.reshape(1, -1))[0][0]
            similarity_tfidf = cosine_similarity(query_tfidf.reshape(1, -1), embedding_tfidf.reshape(1, -1))[0][0]
            results[df_idx] = {'similitud_descripcion': similarity_descripcion,
                               'similitud_allinfo': similarity_allinfo,
                               'similitud_tfidf': similarity_tfidf,
                               'similitud_info': similitudes[i],
                               'precio_msm': precio_msm,
                               'precio_oferta': precio_oferta,
                               'descripcion': descripcion,
                               'search_text': search_text,
                               'proveedor': proveedor}


    sorted_results = []
    for x in results.items():
        consonant_matches = compare_consonant_matches(search_term, x[1]['search_text']).items()
        pc_matches = [y[1]['match_percentage'] for y in consonant_matches]
        pc_matches = np.array([y == 100 for y in pc_matches]).sum() / len(pc_matches)
        if pc_matches >= 0.75:
            sorted_results.append(x)
        
    price_condition = set([x[0] for x in sorted_results if x[1]['precio_msm'] > 0])    
    lower_description_threshold = np.mean([x[1]['similitud_descripcion'] for x in sorted_results]) - 2 * np.std([x[1]['similitud_descripcion'] for x in sorted_results])
    description_condition = set([x[0] for x in sorted_results if x[1]['similitud_descripcion'] > 0.2])
    
    if not(has_prov):
      lower_tfidf_threshold = np.mean([x[1]['similitud_tfidf'] for x in sorted_results]) - 2 * np.std([x[1]['similitud_tfidf'] for x in sorted_results])
      tfidf_condition = set([x[0] for x in sorted_results if x[1]['similitud_tfidf'] > 0.2])
      filter_index = price_condition.intersection(description_condition.intersection(tfidf_condition))

    else:
      filter_index = price_condition.intersection(description_condition)
    
    sorted_results = [x for x in sorted_results if x[0] in filter_index]

    # Ahora ordenamos los resultados por min(precio_msm, precio_oferta)
    sorted_results = sorted(sorted_results, key=lambda x: max(x[1]['similitud_tfidf'], x[1]['similitud_allinfo'], x[1]['similitud_descripcion']), reverse=True)

    sorted_results = sorted_results[:int(len(sorted_results) * 0.95)]

    if orden == "Precio":
      if considerar_ofertas == "Sí":
        # Ahora ordenamos los resultados por min(precio_msm, precio_oferta)
        sorted_results = sorted(sorted_results, key=lambda x: min(x[1]['precio_msm'], x[1]['precio_oferta']), reverse=False)
      else:
        # Ahora ordenamos los resultados por min(precio_msm)
        sorted_results = sorted(sorted_results, key=lambda x: x[1]['precio_msm'], reverse=False)

    elif orden == "Relevancia":
        # Ahora ordenamos los resultados por maxima similitud entre similaridad descripcion, similitud tfidf y similitud allinfo
        sorted_results = sorted(sorted_results, key=lambda x: max(x[1]['similitud_descripcion'], x[1]['similitud_tfidf'], x[1]['similitud_allinfo']), reverse=True)

    if len(sorted_results) > show:
      sorted_results = sorted_results[:show]
    return sorted_results
