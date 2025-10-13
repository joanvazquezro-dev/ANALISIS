"""Tests para sistemas hiperestáticos (múltiples apoyos)."""

import pytest
import numpy as np
from backend.viga import Viga, Apoyo, CargaPuntual, CargaUniforme


class TestSistemasHiperestaticos:
    """Tests para vigas con 3 o más apoyos (estáticamente indeterminados)."""
    
    def test_tres_apoyos_tipo_sistema(self):
        """Sistema con 3 apoyos debe ser hiperestático grado 1."""
        viga = Viga(8.0, 200e9, 1e-5)
        viga.limpiar_apoyos()
        viga.agregar_apoyo(Apoyo(0.0, "A"))
        viga.agregar_apoyo(Apoyo(4.0, "B"))
        viga.agregar_apoyo(Apoyo(8.0, "C"))
        
        assert viga.tipo_sistema() == "hiperestatico"
        assert viga.grado_hiperestaticidad() == 1
    
    def test_tres_apoyos_carga_uniforme(self):
        """Viga continua con 3 apoyos y carga uniforme.
        
        El apoyo central debe tener la mayor reacción.
        """
        viga = Viga(8.0, 200e9, 1e-5)
        viga.limpiar_apoyos()
        viga.agregar_apoyo(Apoyo(0.0, "A"))
        viga.agregar_apoyo(Apoyo(4.0, "B"))
        viga.agregar_apoyo(Apoyo(8.0, "C"))
        viga.agregar_carga(CargaUniforme(3000, 0, 8))
        
        reacciones = viga.calcular_reacciones()
        
        # Verificar equilibrio vertical
        suma_reacciones = sum(reacciones.values())
        suma_cargas = 3000 * 8
        assert abs(suma_reacciones - suma_cargas) < 1e-3, f"Equilibrio falla: ΣR={suma_reacciones}, ΣF={suma_cargas}"
        
        # Apoyo central debe tener mayor reacción (propiedad de viga continua)
        assert reacciones['B'] > reacciones['A'], "Apoyo central debe tener mayor reacción que extremo A"
        assert reacciones['B'] > reacciones['C'], "Apoyo central debe tener mayor reacción que extremo C"
        
        # Por simetría, reacciones en extremos deben ser iguales
        assert abs(reacciones['A'] - reacciones['C']) < 1e-2, "Reacciones en extremos deben ser simétricas"
    
    def test_tres_apoyos_carga_puntual_centrada(self):
        """Carga puntual en el centro (sobre apoyo B)."""
        L = 6.0
        viga = Viga(L, 210e9, 8e-6)
        viga.limpiar_apoyos()
        viga.agregar_apoyo(Apoyo(0.0, "A"))
        viga.agregar_apoyo(Apoyo(L/2, "B"))
        viga.agregar_apoyo(Apoyo(L, "C"))
        viga.agregar_carga(CargaPuntual(10000, L/2))
        
        reacciones = viga.calcular_reacciones()
        
        # Verificar equilibrio
        assert abs(sum(reacciones.values()) - 10000) < 1e-3
        
        # La mayor parte de la carga debe ser soportada por el apoyo B
        assert reacciones['B'] > 0.5 * 10000, "Apoyo B debe soportar >50% de carga centrada"
    
    def test_cuatro_apoyos_equidistantes(self):
        """Sistema hiperestático grado 2 con 4 apoyos."""
        L = 9.0
        viga = Viga(L, 210e9, 8e-6)
        viga.limpiar_apoyos()
        viga.agregar_apoyo(Apoyo(0, "A"))
        viga.agregar_apoyo(Apoyo(3, "B"))
        viga.agregar_apoyo(Apoyo(6, "C"))
        viga.agregar_apoyo(Apoyo(9, "D"))
        
        assert viga.tipo_sistema() == "hiperestatico"
        assert viga.grado_hiperestaticidad() == 2
        
        viga.agregar_carga(CargaPuntual(10000, L/2))  # x=4.5m
        
        reacciones = viga.calcular_reacciones()
        
        # Verificar equilibrio
        suma_R = sum(reacciones.values())
        assert abs(suma_R - 10000) < 1e-3, f"Equilibrio falla: ΣR={suma_R}"
        
        # Todas las reacciones deben ser positivas (apoyos, no tensión)
        for nombre, R in reacciones.items():
            assert R > -1e-3, f"Reacción {nombre} es negativa: {R}"
    
    def test_cinco_apoyos_carga_uniforme(self):
        """Sistema hiperestático grado 3 con 5 apoyos."""
        L = 12.0
        viga = Viga(L, 200e9, 1.2e-5)
        viga.limpiar_apoyos()
        for i in range(5):
            viga.agregar_apoyo(Apoyo(i * L/4, chr(65 + i)))  # A, B, C, D, E
        
        assert viga.grado_hiperestaticidad() == 3
        
        viga.agregar_carga(CargaUniforme(4000, 0, L))
        
        reacciones = viga.calcular_reacciones()
        
        # Verificar equilibrio
        suma_R = sum(reacciones.values())
        suma_F = 4000 * L
        error_rel = abs(suma_R - suma_F) / suma_F
        assert error_rel < 1e-3, f"Error equilibrio: {error_rel*100:.4f}%"
    
    def test_validacion_sistema_hiperestatico(self):
        """Validar sistema hiperestático retorna información correcta."""
        viga = Viga(6.0, 210e9, 8e-6)
        viga.limpiar_apoyos()
        viga.agregar_apoyo(Apoyo(0, "A"))
        viga.agregar_apoyo(Apoyo(2, "B"))
        viga.agregar_apoyo(Apoyo(4, "C"))
        viga.agregar_apoyo(Apoyo(6, "D"))
        
        validacion = viga.validar_sistema()
        
        assert validacion['valido'] is True
        assert validacion['tipo'] == 'hiperestatico'
        assert validacion['grado'] == 2
        assert len(validacion['mensajes']) > 0
        assert any('hiperestático' in msg for msg in validacion['mensajes'])


class TestComparacionMetodos:
    """Comparar método simbólico vs numérico."""
    
    def test_consistencia_simbolico_numerico(self):
        """Para sistema simple, ambos métodos deben coincidir."""
        viga = Viga(6.0, 210e9, 8e-6)
        viga.agregar_carga(CargaUniforme(5000, 0, 6))
        
        # Intentar método simbólico
        try:
            res_simbolico = viga.evaluar(num_puntos=200)
        except:
            pytest.skip("Método simbólico no disponible")
        
        # Forzar método numérico
        res_numerico = viga._evaluar_numerico(num_puntos=200)
        
        # Comparar deflexiones
        y_sim = np.array(res_simbolico['deflexion'])
        y_num = np.array(res_numerico['deflexion'])
        
        error_max = np.max(np.abs(y_sim - y_num))
        error_rel = error_max / (np.max(np.abs(y_sim)) + 1e-12)
        
        assert error_rel < 0.01, f"Métodos difieren >1%: error_rel={error_rel*100:.2f}%"


class TestCondicionesContorno:
    """Verificar condiciones de contorno (deflexión en apoyos)."""
    
    def test_deflexion_nula_en_apoyos_dos(self):
        """Deflexión debe ser ~0 en ambos apoyos (2 apoyos)."""
        viga = Viga(6.0, 210e9, 8e-6)
        viga.agregar_carga(CargaPuntual(5000, 3))
        
        resultados = viga.evaluar(num_puntos=500)
        x_vals = np.array(resultados['x'])
        y_vals = np.array(resultados['deflexion'])
        
        # Encontrar deflexiones en apoyos
        idx_A = np.argmin(np.abs(x_vals - 0.0))
        idx_B = np.argmin(np.abs(x_vals - 6.0))
        
        y_A = abs(y_vals[idx_A])
        y_B = abs(y_vals[idx_B])
        
        # Tolerancia: 0.1 mm
        assert y_A < 1e-4, f"Deflexión en A = {y_A*1000:.4f} mm (debe ser ~0)"
        assert y_B < 1e-4, f"Deflexión en B = {y_B*1000:.4f} mm (debe ser ~0)"
    
    def test_deflexion_nula_en_apoyos_tres(self):
        """Deflexión debe ser ~0 en todos los apoyos (3 apoyos)."""
        L = 6.0
        viga = Viga(L, 210e9, 8e-6)
        viga.limpiar_apoyos()
        viga.agregar_apoyo(Apoyo(0, "A"))
        viga.agregar_apoyo(Apoyo(L/2, "B"))
        viga.agregar_apoyo(Apoyo(L, "C"))
        viga.agregar_carga(CargaUniforme(3000, 0, L))
        
        resultados = viga.evaluar(num_puntos=600)
        x_vals = np.array(resultados['x'])
        y_vals = np.array(resultados['deflexion'])
        
        for apoyo in viga.apoyos:
            idx = np.argmin(np.abs(x_vals - apoyo.posicion))
            y_apoyo = abs(y_vals[idx])
            assert y_apoyo < 1e-4, f"Deflexión en {apoyo.nombre} = {y_apoyo*1000:.4f} mm (debe ser ~0)"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
