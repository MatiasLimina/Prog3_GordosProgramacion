package Ejercicio_06;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Objects;

public abstract class EspecieAnimal extends Especie {
    private String periodoCelo;
    private List<Especie> alimentos; // Asociación reflexiva: animales o vegetales que sirven de alimento

    public EspecieAnimal(String nombreCientifico, String nombreVulgar, String periodoCelo) {
        super(nombreCientifico, nombreVulgar);
        Objects.requireNonNull(periodoCelo, "El período de celo no puede ser nulo");
        this.periodoCelo = periodoCelo;
        this.alimentos = new ArrayList<>();
    }

    public void agregarAlimento(Especie especieAlimento) {
        Objects.requireNonNull(especieAlimento, "La especie de alimento no puede ser nula");
        if (!alimentos.contains(especieAlimento)) {
            alimentos.add(especieAlimento);
        }
    }

    public String getPeriodoCelo() {
        return periodoCelo;
    }

    public void setPeriodoCelo(String periodoCelo) {
        Objects.requireNonNull(periodoCelo, "El período de celo no puede ser nulo");
        this.periodoCelo = periodoCelo;
    }

    public List<Especie> getAlimentos() {
        return Collections.unmodifiableList(alimentos);
    }
}
