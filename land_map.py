import pandas as pd
import folium
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import time
import webbrowser
import os

# Configurações otimizadas
geolocator = Nominatim(user_agent="lawton_land_map", timeout=10)
geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)

def safe_geocode(address):
    try:
        location = geocode(address)
        return (location.latitude, location.longitude) if location else (None, None)
    except Exception:
        return (None, None)

# 1. Carregar o arquivo CSV
df = pd.read_csv('mls_land.csv')

# 2. Filtrar os dados
lawton_active = df[
    (df['City'].str.lower() == 'lawton') & 
    (df['Status'].str.lower() == 'active')
].copy()

print(f"Total de terrenos ativos em Lawton: {len(lawton_active)}")

# 3. Preparar endereços
lawton_active['Full_Address'] = (
    lawton_active['Address'] + ', ' + 
    'Lawton, OK, ' + 
    lawton_active['Zip'].astype(str)
)

# 4. Geocodificação rápida
print("\nGeocodificando endereços...")
coordinates = []
for address in lawton_active['Full_Address']:
    lat, lon = safe_geocode(address)
    coordinates.append((lat, lon))
    time.sleep(1)

lawton_active[['Latitude', 'Longitude']] = pd.DataFrame(coordinates, index=lawton_active.index)
lawton_active = lawton_active.dropna(subset=['Latitude', 'Longitude'])

print(f"\nTerrenos geocodificados com sucesso: {len(lawton_active)}")

# 5. Criar o mapa
if not lawton_active.empty:
    # Mapa compartilhável
    m = folium.Map(
        location=[lawton_active['Latitude'].mean(), lawton_active['Longitude'].mean()],
        zoom_start=12,
        tiles='https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
        attr='Map data © OpenStreetMap contributors'
    )
    
    # Adicionar marcadores
    for _, row in lawton_active.iterrows():
        popup_text = f"""
        <b>MLS #:</b> {row.get('MLS #', 'N/A')}<br>
        <b>Address:</b> {row.get('Address', 'N/A')}<br>
        <b>Price:</b> {row.get('Price', 'N/A')}<br>
        <b>Lot Size:</b> {row.get('LtSize', 'N/A')}<br>
        <b>Area:</b> {row.get('Area', 'N/A')}
        """
        
        folium.Marker(
            location=[row['Latitude'], row['Longitude']],
            popup=folium.Popup(popup_text, max_width=250),
            icon=folium.Icon(color='green', icon='home', prefix='fa')
        ).add_to(m)
    
    # Salvar outputs
    m.save('lawton_land_map.html')
    lawton_active.to_csv('lawton_land_results.csv', index=False)
    
    print("\nArquivos criados com sucesso:")
    print(f"- Mapa interativo: lawton_land_map.html")
    print(f"- Resultados em CSV: lawton_land_results.csv")
    
    # Abrir o mapa automaticamente
    webbrowser.open('file://' + os.path.abspath('lawton_land_map.html'))
else:
    print("Nenhum terreno foi geocodificado com sucesso.")