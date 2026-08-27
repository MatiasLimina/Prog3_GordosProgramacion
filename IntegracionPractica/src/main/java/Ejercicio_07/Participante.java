package Ejercicio_07;

import java.util.ArrayList;
import java.util.List;

public abstract class Participante {
    protected List<Inscripcion> inscripciones;

    public Participante() {
        this.inscripciones = new ArrayList<>();
    }

    public List<Inscripcion> getInscripciones() {
        return inscripciones;
    }

    public void agregarInscripcion(Inscripcion inscripcion) {
        if (!this.inscripciones.contains(inscripcion)) {
            this.inscripciones.add(inscripcion);
        }
    }
}
