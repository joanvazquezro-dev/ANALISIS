"""Tests para sistemas básicos (isostáticos)."""

import pytest
import numpy as np
from backend.viga import Viga, Apoyo, CargaPuntual, CargaUniforme, CargaMomento, CargaTriangular


class TestSistemasIsostaticos:
    """Tests para sistemas con 2 apoyos (estáticamente determinados)."""
    
    def test_carga_puntual_centrada(self):
        """Carga puntual P=1000N en el centro de viga L=6m.
        
        Solución teórica:
        - RA = RB = P/2 = 500 N
        - M_max = P*L/4 = 1500 N·m
        """
        viga = Viga(longitud=6.0, E=210e9, I=8e-6)
        viga.agregar_carga(CargaPuntual(magnitud=1000, posicion=3.0))
        
        reacciones = viga.calcular_reacciones()
        
        # Verificar reacciones por simetría
        assert abs(reacciones['A'] - 500) < 1e-6, "Reacción en A incorrecta"
        assert abs(reacciones['B'] - 500) < 1e-6, "Reacción en B incorrecta"
        
        # Verificar equilibrio vertical
        suma_R = sum(reacciones.values())
        assert abs(suma_R - 1000) < 1e-6, "No se cumple equilibrio vertical"
    
    def test_carga_puntual_asimetrica(self):
        """Carga puntual P=2000N en x=2m de viga L=6m.
        
        Solución teórica:
        - RB = P*a/L = 2000*2/6 = 666.67 N
        - RA = P - RB = 1333.33 N
        """
        viga = Viga(6.0, 210e9, 8e-6)
        viga.agregar_carga(CargaPuntual(magnitud=2000, posicion=2.0))
        
        reacciones = viga.calcular_reacciones()
        
        # Valores teóricos
        R_B_teorico = 2000 * 2 / 6  # 666.67
        R_A_teorico = 2000 - R_B_teorico  # 1333.33
        
        assert abs(reacciones['A'] - R_A_teorico) < 1e-3
        assert abs(reacciones['B'] - R_B_teorico) < 1e-3
    
    def test_carga_uniforme_completa(self):
        """Carga uniforme w=5000N/m en toda la viga L=6m.
        
        Solución teórica:
        - Carga total = w*L = 30000 N
        - RA = RB = w*L/2 = 15000 N
        """
        viga = Viga(6.0, 210e9, 8e-6)
        viga.agregar_carga(CargaUniforme(intensidad=5000, inicio=0, fin=6))
        
        reacciones = viga.calcular_reacciones()
        
        assert abs(reacciones['A'] - 15000) < 1e-3
        assert abs(reacciones['B'] - 15000) < 1e-3
    
    def test_carga_uniforme_parcial(self):
        """Carga uniforme w=3000N/m entre x=1m y x=4m (L=3m de longitud)."""
        viga = Viga(6.0, 210e9, 8e-6)
        viga.agregar_carga(CargaUniforme(intensidad=3000, inicio=1, fin=4))
        
        reacciones = viga.calcular_reacciones()
        
        # Carga total: 3000*3 = 9000 N actuando en x=2.5m
        P_total = 3000 * 3
        x_centro = 2.5
        
        # RB = P_total * x_centro / L
        R_B_teorico = P_total * x_centro / 6.0  # 3750 N
        R_A_teorico = P_total - R_B_teorico  # 5250 N
        
        assert abs(reacciones['A'] - R_A_teorico) < 1e-2
        assert abs(reacciones['B'] - R_B_teorico) < 1e-2
    
    def test_momento_puntual_en_apoyo(self):
        """Momento concentrado M=5000 N·m en apoyo con en_vano=False.
        
        El momento en el apoyo NO debe crear salto en M(x) interior.
        """
        viga = Viga(6.0, 210e9, 8e-6)
        viga.agregar_carga(CargaMomento(magnitud=5000, posicion=0.0, en_vano=False))
        
        # El momento solo afecta las reacciones, no crea salto interno
        reacciones = viga.calcular_reacciones()
        
        # Debe cumplir equilibrio de momentos
        assert abs(reacciones['A'] + reacciones['B']) < 100  # Suma ~0 (solo momento, no fuerza)
    
    def test_momento_puntual_en_vano(self):
        """Momento concentrado M=3000 N·m en x=3m (centro) con en_vano=True."""
        viga = Viga(6.0, 210e9, 8e-6)
        viga.agregar_carga(CargaMomento(magnitud=3000, posicion=3.0, en_vano=True))
        
        reacciones = viga.calcular_reacciones()
        
        # Un par no produce fuerza vertical neta
        # RA + RB ≈ 0, pero RA·L - M = RB·L
        suma_fuerzas = abs(reacciones['A'] + reacciones['B'])
        assert suma_fuerzas < 100, f"Momento puntual no debe crear fuerza neta vertical, obtenido={suma_fuerzas}"
    
    def test_carga_triangular_creciente(self):
        """Carga triangular de 0 a w0=4000 N/m en toda la viga."""
        viga = Viga(6.0, 210e9, 8e-6)
        viga.agregar_carga(CargaTriangular(intensidad_inicio=0, intensidad_fin=4000, inicio=0, fin=6))
        
        reacciones = viga.calcular_reacciones()
        
        # Carga total: (0 + 4000)/2 * 6 = 12000 N
        # Centro de masa: x = L * (0 + 2*4000) / (3*(0 + 4000)) = 4m
        P_total = 12000
        x_centroide = 4.0
        
        R_B_teorico = P_total * x_centroide / 6.0  # 8000 N
        R_A_teorico = P_total - R_B_teorico  # 4000 N
        
        assert abs(reacciones['A'] - R_A_teorico) < 1e-1
        assert abs(reacciones['B'] - R_B_teorico) < 1e-1
    
    def test_cargas_multiples_superposicion(self):
        """Dos cargas simultáneas: puntual + uniforme."""
        viga = Viga(6.0, 210e9, 8e-6)
        viga.agregar_carga(CargaPuntual(magnitud=2000, posicion=2.0))
        viga.agregar_carga(CargaUniforme(intensidad=1000, inicio=0, fin=6))
        
        reacciones = viga.calcular_reacciones()
        
        # Carga total: 2000 + 1000*6 = 8000 N
        suma_R = sum(reacciones.values())
        assert abs(suma_R - 8000) < 1e-3, "Equilibrio vertical falla con cargas múltiples"


class TestValidacionesSistema:
    """Tests de validación de entrada y configuración."""
    
    def test_tipo_sistema_dos_apoyos(self):
        """Sistema con 2 apoyos debe ser isostático."""
        viga = Viga(6.0, 210e9, 8e-6)  # 2 apoyos por defecto
        
        assert viga.tipo_sistema() == "isostatico"
        assert viga.grado_hiperestaticidad() == 0
    
    def test_validacion_sistema_completa(self):
        """La función validar_sistema debe retornar estructura correcta."""
        viga = Viga(6.0, 210e9, 8e-6)
        validacion = viga.validar_sistema()
        
        assert 'valido' in validacion
        assert 'tipo' in validacion
        assert 'grado' in validacion
        assert 'mensajes' in validacion
        assert 'advertencias' in validacion
        
        assert validacion['valido'] is True
        assert validacion['tipo'] == 'isostatico'
    
    def test_carga_fuera_de_viga(self):
        """Debe rechazar cargas fuera del dominio."""
        viga = Viga(6.0, 210e9, 8e-6)
        
        with pytest.raises(ValueError, match="fuera de la viga"):
            viga.agregar_carga(CargaPuntual(1000, 7.0))
    
    def test_apoyo_fuera_de_viga(self):
        """Debe rechazar apoyos fuera del dominio."""
        viga = Viga(6.0, 210e9, 8e-6)
        
        with pytest.raises(ValueError, match="fuera de la viga"):
            viga.agregar_apoyo(Apoyo(posicion=7.0, nombre="C"))
    
    def test_apoyos_muy_cercanos(self):
        """Debe rechazar apoyos con distancia < 1mm."""
        viga = Viga(6.0, 210e9, 8e-6)
        viga.limpiar_apoyos()
        viga.agregar_apoyo(Apoyo(3.0, "A"))
        
        with pytest.raises(ValueError, match="muy cercano"):
            viga.agregar_apoyo(Apoyo(3.0005, "B"))  # 0.5mm de separación
    
    def test_longitud_negativa(self):
        """Debe rechazar longitud no positiva."""
        with pytest.raises(ValueError, match="longitud"):
            Viga(longitud=-1.0, E=210e9, I=8e-6)
    
    def test_E_negativo(self):
        """Debe rechazar módulo E no positivo."""
        with pytest.raises(ValueError, match="elasticidad"):
            Viga(longitud=6.0, E=-210e9, I=8e-6)
    
    def test_I_negativo(self):
        """Debe rechazar inercia no positiva."""
        with pytest.raises(ValueError, match="inercia"):
            Viga(longitud=6.0, E=210e9, I=-8e-6)


class TestPropiedadesGeometricas:
    """Tests de propiedades geométricas de cargas."""
    
    def test_carga_uniforme_longitud(self):
        """Propiedad longitud de CargaUniforme."""
        carga = CargaUniforme(intensidad=2000, inicio=1, fin=4)
        assert carga.longitud == 3.0
    
    def test_carga_trapezoidal_pendiente(self):
        """Propiedad pendiente de CargaTrapezoidal."""
        from backend.viga import CargaTrapezoidal
        carga = CargaTrapezoidal(intensidad_inicio=1000, intensidad_fin=4000, inicio=0, fin=6)
        assert abs(carga.pendiente - 500) < 1e-6  # (4000-1000)/6 = 500
    
    def test_total_load_carga_puntual(self):
        """Método total_load de CargaPuntual."""
        carga = CargaPuntual(magnitud=5000, posicion=3.0)
        assert carga.total_load() == 5000
    
    def test_total_load_carga_uniforme(self):
        """Método total_load de CargaUniforme."""
        carga = CargaUniforme(intensidad=2000, inicio=0, fin=5)
        assert carga.total_load() == 10000  # 2000 * 5


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
