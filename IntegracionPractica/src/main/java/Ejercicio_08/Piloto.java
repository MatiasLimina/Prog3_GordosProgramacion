package Ejercicio_08;

import java.util.ArrayList;
import java.util.List;

public class Piloto extends Persona {
    private String numeroLicencia;
    private String restricciones;
    private List<TipoAvion> tiposAutorizados;

    public Piloto(String nss, String nombre, String direccion, String telefono, String numeroLicencia, String restricciones) {
        super(nss, nombre, direccion, telefono);
        this.numeroLicencia = numeroLicencia;
        this.restricciones = restricciones;
        this.tiposAutorizados = new ArrayList<>();
    }

    public void agregarTipoAutorizado(TipoAvion t) {
        if (!tiposAutorizados.contains(t)) {
            tiposAutorizados.add(t);
        }
    }

    public void removerTipoAutorizado(TipoAvion t) {
        tiposAutorizados.remove(t);
    }

    public String getNumeroLicencia() { return numeroLicencia; }
    public void setNumeroLicencia(String numeroLicencia) { this.numeroLicencia = numeroLicencia; }

    public String getRestricciones() { return restricciones; }
    public void setRestricciones(String restricciones) { this.restricciones = restricciones; }

    public List<TipoAvion> getTiposAutorizados() { return tiposAutorizados; }
}
