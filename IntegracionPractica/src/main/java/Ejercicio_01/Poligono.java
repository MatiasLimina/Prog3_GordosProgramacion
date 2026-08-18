package Ejercicio_01;

import java.util.Collections;
import java.util.List;

public abstract class Poligono extends  Figura {
    private List<Lado> lados;

    public Poligono(List<Lado> lados) {
        this.lados = lados;
    }

    public List<Lado> getLados() {
        return Collections.unmodifiableList(lados);
    }

    public void setLados(List<Lado> lados) {
        this.lados = lados;
    }
}
