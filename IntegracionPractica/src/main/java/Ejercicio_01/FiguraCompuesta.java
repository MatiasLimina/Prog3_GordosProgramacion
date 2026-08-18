package Ejercicio_01;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

public class FiguraCompuesta extends Figura{
    private List<Figura> figuras;

    public FiguraCompuesta(List<Figura> figuras) {
        this.figuras = new ArrayList<>();
    }

    public agregarFigura(){
        figuras.add(new figura());
    }
    public List<Figura> getFiguras() {
        return Collections.unmodifiableList(figuras);
    }

    public void setFiguras(List<Figura> figuras) {
        this.figuras = figuras;
    }
}
