package Ejercicio_09;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Objects;

public class Museo {
    private String nombre;
    private List<ObjetoDeArte> coleccion; // Composición 1 — 0..*
    private List<Exposicion> exposiciones; // Composición 1 — 0..*
    private List<ColeccionExterna> coleccionesExternas; // Asociación para intercambio

    public Museo(String nombre) {
        Objects.requireNonNull(nombre, "El nombre del museo no puede ser nulo");
        this.nombre = nombre;
        this.coleccion = new ArrayList<>();
        this.exposiciones = new ArrayList<>();
        this.coleccionesExternas = new ArrayList<>();
    }

    public void agregarObjeto(ObjetoDeArte objeto) {
        Objects.requireNonNull(objeto, "El objeto de arte no puede ser nulo");
        if (!coleccion.contains(objeto)) {
            coleccion.add(objeto);
        }
    }

    public void agregarExposicion(Exposicion exposicion) {
        Objects.requireNonNull(exposicion, "La exposición no puede ser nula");
        if (!exposiciones.contains(exposicion)) {
            exposiciones.add(exposicion);
        }
    }

    public void agregarColeccionExterna(ColeccionExterna coleccionExterna) {
        Objects.requireNonNull(coleccionExterna, "La colección externa no puede ser nula");
        if (!coleccionesExternas.contains(coleccionExterna)) {
            coleccionesExternas.add(coleccionExterna);
        }
    }

    public String getNombre() {
        return nombre;
    }

    public List<ObjetoDeArte> getColeccion() {
        return Collections.unmodifiableList(coleccion);
    }

    public List<Exposicion> getExposiciones() {
        return Collections.unmodifiableList(exposiciones);
    }

    public List<ColeccionExterna> getColeccionesExternas() {
        return Collections.unmodifiableList(coleccionesExternas);
    }

    public void mostrarResumen() {
        System.out.println("=== MUSEO: " + nombre + " ===");
        System.out.println("Obras en colección/gestión: " + coleccion.size());
        for (ObjetoDeArte obj : coleccion) {
            String tipoEstado = obj.getEstadoTenencia() instanceof Permanente ? "Permanente" : "Préstamo";
            String artistaNombre = obj.getArtista() != null ? obj.getArtista().getNombre() : "Anónimo";
            System.out.println(" - [" + obj.getIdIdentificacion() + "] " + obj.getTitulo() + 
                    " (" + obj.getClass().getSimpleName() + "), Artista: " + artistaNombre + 
                    ", Estado: " + tipoEstado);
        }
        System.out.println("Exposiciones organizadas: " + exposiciones.size());
        for (Exposicion exp : exposiciones) {
            System.out.println(" - " + exp.getNombre() + " (" + exp.getFechaComienzo() + " al " + exp.getFechaFinalizacion() + "), Obras exhibidas: " + exp.getObjetosExhibidos().size());
        }
        System.out.println("Colecciones externas asociadas: " + coleccionesExternas.size());
        for (ColeccionExterna ce : coleccionesExternas) {
            System.out.println(" - " + ce.getNombre() + " (" + ce.getTipoColeccion() + ")");
        }
    }
}
