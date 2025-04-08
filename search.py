import numpy as np
import pandas as pd

def key_search(nsearch, options, df, considerar_ofertas, considerar_descripcion, buscar_en_prov):

    search_bool = True

    if buscar_en_prov != []:
        df = df[df['Proveedor'].isin(buscar_en_prov)]
        if options[f'search_{0}'].strip() == '':                  
          if considerar_ofertas == "Sí":
              # Agregar una columna auxiliar con el menor valor entre A y B
              df['Min_Val'] = df[['Precio MSM', 'Precio Oferta']].min(axis=1)

              # Ordenar según la nueva columna
              df = df.sort_values(by=['Min_Val', 'Descripcion'], ascending=True)

              # Eliminar la columna auxiliar si no se necesita
              df = df.drop(columns=['Min_Val'])
          else:
              df = df.sort_values(by=['Precio MSM', 'Descripcion'], ascending=True)

          df = df[df['Precio MSM'] > 0]
          df = df.drop(columns=['search_text'])
          return df

    if options[f'search_{0}'] == '':
        return False
    df['search_text'] = df['search_text'].fillna('')
    if options[f'contains_{0}'] == 'Contiene':
        search_bool = (df['search_text'].str.lower().str.contains(options[f'search_{0}'].lower()))
    else:
        search_bool = ~(df['search_text'].str.lower().str.contains(options[f'search_{0}'].lower()))

    if not considerar_descripcion:
      for i in range(1, nsearch):
          if options[f'search_{i}'] != '':
            if options[f'logical_{i}'] == 'Y':
                if options[f'contains_{i}'] == 'Contiene':                
                    search_bool = search_bool & (df['search_text'].str.lower().str.contains(options[f'search_{i}'].lower()))
                else:
                    search_bool = search_bool & (~(df['search_text'].str.lower().str.contains(options[f'search_{i}'].lower())))
            elif options[f'logical_{i}'] == 'O':
                if options[f'contains_{i}'] == 'Contiene':
                    search_bool = search_bool | (df['search_text'].str.lower().str.contains(options[f'search_{i}'].lower()))
                else:
                    search_bool = search_bool | (~(df['search_text'].str.lower().str.contains(options[f'search_{i}'].lower())))
          else:
              break
    else:
        for i in range(1, nsearch):
            if options[f'search_{i}'] != '':
                if options[f'logical_{i}'] == 'Y':
                    if options[f'contains_{i}'] == 'Contiene':
                        search_bool = search_bool & (df['Descripcion'].str.lower().str.contains(options[f'search_{i}'].lower()))
                    else:
                        search_bool = search_bool & (~(df['Descripcion'].str.lower().str.contains(options[f'search_{i}'].lower())))
                elif options[f'logical_{i}'] == 'O':
                    if options[f'contains_{i}'] == 'Contiene':
                        search_bool = search_bool | (df['Descripcion'].str.lower().str.contains(options[f'search_{i}'].lower()))
                    else:
                        search_bool = search_bool | (~(df['Descripcion'].str.lower().str.contains(options[f'search_{i}'].lower())))
            else:
                break

                        

    df = df[search_bool].drop(columns=['search_text'])

    if considerar_ofertas == "Sí":
        # Agregar una columna auxiliar con el menor valor entre A y B
        df['Min_Val'] = df[['Precio MSM', 'Precio Oferta']].min(axis=1)

        # Ordenar según la nueva columna
        df = df.sort_values(by=['Min_Val', 'Descripcion'], ascending=True)

        # Eliminar la columna auxiliar si no se necesita
        df = df.drop(columns=['Min_Val'])
    else:
        df = df.sort_values(by=['Precio MSM', 'Descripcion'], ascending=True)

    df = df[df['Precio MSM'] > 0]
    return df


