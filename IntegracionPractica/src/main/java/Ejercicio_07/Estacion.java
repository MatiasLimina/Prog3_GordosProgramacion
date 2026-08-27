package Ejercicio_07;

import java.util.ArrayList;
import java.util.List;

public class Estacion {
    private String codigoIdentificativo;
    private String nombre;
    private String direccion;
    private String telefono;
    private float totalKmEsquiables;
    private List<String> personasContacto;
    private List<Pista> pistas; // Composición fuerte
    private List<Federacion> federacionesAdmin;

    public Estacion(String codigoIdentificativo, String nombre, String direccion, String telefono, float totalKmEsquiables) {
        this.codigoIdentificativo = codigoIdentificativo;
        this.nombre = nombre;
        this.direccion = direccion;
        this.telefono = telefono;
        this.totalKmEsquiables = totalKmEsquiables;
        this.personasContacto = new ArrayList<>();
        this.pistas = new ArrayList<>();
        this.federacionesAdmin = new ArrayList<>();
    }

    public int getNumeroPistas() {
        return this.pistas.size();
    }

    public Pista crearPista(float longitudKm, String nivelDificultad) {
        String codigoPista = this.codigoIdentificativo + "-" + (this.pistas.size() + 1);
        Pista pista = new Pista(codigoPista, longitudKm, nivelDificultad, this);
        this.pistas.add(pista);
        return pista;
    }

    public void agregarFederacion(Federacion federacion) {
        if (!this.federacionesAdmin.contains(federacion)) {
            this.federacionesAdmin.add(federacion);
        }
    }

    public void agregarPersonaContacto(String persona) {
        this.personasContacto.add(persona);
    }

    public String getCodigoIdentificativo() {
        return codigoIdentificativo;
    }

    public void setCodigoIdentificativo(String codigoIdentificativo) {
        this.codigoIdentificativo = codigoIdentificativo;
    }

    public String getNombre() {
        return nombre;
    }

    public void setNombre(String nombre) {
        this.nombre = nombre;
    }

    public String getDireccion() {
        return direccion;
    }

    public void setDireccion(String direccion) {
        this.direccion = direccion;
    }

    public String getTelefono() {
        return telefono;
    }

    public void setTelefono(String telefono) {
        this.telefono = telefono;
    }

    public float getTotalKmEsquiables() {
        return totalKmEsquiables;
    }

    public void setTotalKmEsquiables(float totalKmEsquiables) {
        this.totalKmEsquiables = totalKmEsquiables;
    }

    public List<String> getPersonasContacto() {
        return personasContacto;
    }

    public List<Pista> getPistas() {
        return pistas;
    }

    public List<Federacion> getFederacionesAdmin() {
        return federacionesAdmin;
    }

    @Override
    public String toString() {
        return nombre + " (" + codigoIdentificativo + ")";
    }
}
