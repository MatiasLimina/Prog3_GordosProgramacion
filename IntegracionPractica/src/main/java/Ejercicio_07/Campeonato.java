package Ejercicio_07;

import java.util.ArrayList;
import java.util.List;

public class Campeonato {
    private List<Prueba> pruebas; // Composición fuerte

    public Campeonato() {
        this.pruebas = new ArrayList<>();
    }

    public void agregarPrueba(Prueba prueba) {
        if (!this.pruebas.contains(prueba)) {
            this.pruebas.add(prueba);
        }
    }

    public List<Prueba> getPruebas() {
        return pruebas;
    }
}
