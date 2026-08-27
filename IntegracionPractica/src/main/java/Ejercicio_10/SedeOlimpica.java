package Ejercicio_10;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Objects;

public class SedeOlimpica {
    private double presupuestoAproximado;
    private List<ComplejoDeportivo> complejos; // Composición 1 — 1..*

    public SedeOlimpica(double presupuestoAproximado, List<ComplejoDeportivo> complejos) {
        Objects.requireNonNull(complejos, "La lista de complejos no puede ser nula");
        if (complejos.isEmpty()) {
            throw new IllegalArgumentException("Una sede olímpica debe tener al menos un complejo deportivo (1..*)");
        }
        this.presupuestoAproximado = presupuestoAproximado;
        this.complejos = new ArrayList<>(complejos);
    }

    public void agregarComplejo(ComplejoDeportivo complejo) {
        Objects.requireNonNull(complejo, "El complejo deportivo no puede ser nulo");
        if (!complejos.contains(complejo)) {
            complejos.add(complejo);
        }
    }

    public int getNumeroComplejos() {
        return complejos.size();
    }

    public double getPresupuestoAproximado() {
        return presupuestoAproximado;
    }

    public void setPresupuestoAproximado(double presupuestoAproximado) {
        this.presupuestoAproximado = presupuestoAproximado;
    }

    public List<ComplejoDeportivo> getComplejos() {
        return Collections.unmodifiableList(complejos);
    }

    public void setComplejos(List<ComplejoDeportivo> complejos) {
        Objects.requireNonNull(complejos, "La lista de complejos no puede ser nula");
        if (complejos.isEmpty()) {
            throw new IllegalArgumentException("Una sede olímpica debe tener al menos un complejo deportivo");
        }
        this.complejos = new ArrayList<>(complejos);
    }
}
