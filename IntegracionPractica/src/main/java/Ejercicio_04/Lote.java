package Ejercicio_04;

import java.util.ArrayList;
import java.util.List;

public class Lote {
    private List<Mineral> mineralesTierra;
    private Cereal cerealAnterior; // Puede ser null si el lote es virgen

    public Lote(Cereal cerealAnterior) {
        this.mineralesTierra = new ArrayList<>();
        this.cerealAnterior = cerealAnterior;
    }

    public void agregarMineral(Mineral m) {
        mineralesTierra.add(m);
    }

    // Verifica si el lote es especial (si contiene al menos un mineral primario)
    public boolean esEspecial() {
        for (Mineral m : mineralesTierra) {
            if (m.esPrimario()) {
                return true;
            }
        }
        return false;
    }

    // Verifica si el lote tiene todos los minerales de la lista recibida
    public boolean tieneMinerales(List<Mineral> requeridos) {
        return mineralesTierra.containsAll(requeridos);
    }

    public Cereal getCerealAnterior() {
        return cerealAnterior;
    }
}
