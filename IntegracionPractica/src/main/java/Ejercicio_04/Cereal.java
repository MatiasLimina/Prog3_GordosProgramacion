package Ejercicio_04;

import java.util.ArrayList;
import java.util.List;

public abstract class Cereal {
    protected String nombre;
    protected List<Mineral> mineralesRequeridos;

    public Cereal(String nombre) {
        this.nombre = nombre;
        this.mineralesRequeridos = new ArrayList<>();
    }

    public void agregarRequisito(Mineral m) {
        mineralesRequeridos.add(m);
    }

    // Verifica en que lotes puede ser sembrado
    public boolean puedeSembrarseEn(Lote lote) {
        return lote.tieneMinerales(mineralesRequeridos);
    }

    public String getNombre() { return nombre; }
}
