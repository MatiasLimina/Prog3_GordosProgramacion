package Ejercicio_04;

import java.util.ArrayList;
import java.util.List;

public class Cooperativa {
    private List<Cereal> catalogoCereales;

    public Cooperativa() {

        this.catalogoCereales = new ArrayList<>();
    }

    public void agregarCerealAlCatalogo(Cereal c) {
        catalogoCereales.add(c);
    }

    // Aconseja qué cereales se pueden sembrar en un lote determinado
    public List<Cereal> aconsejarCereales(Lote lote) {
        List<Cereal> recomendados = new ArrayList<>();

        for (Cereal cereal : catalogoCereales) {

            // Recorre el catálogo de cereales y verifica si se puede sembrar en determinado lote
            if (cereal.puedeSembrarseEn(lote)) {
                recomendados.add(cereal);
            }
        }

        return recomendados;
    }
}