package Ejercicio_05;

import java.util.ArrayList;
import java.util.List;

public class Persona {
    private String nombre;
    private List<Restaurante> restaurantesFrecuentes;
    private List<Gusto> gustos; // Gustos de cada persona dependiendo el plato y el restaurante

    public Persona(String nombre) {
        this.nombre = nombre;
        this.restaurantesFrecuentes = new ArrayList<>();
        this.gustos = new ArrayList<>();
    }

    // Si una persona visita un restaurante nuevo este ultimo se añade a los restaurantes frecuentados por la persona
    public void frecuentar(Restaurante restaurante) {
        if (!restaurantesFrecuentes.contains(restaurante)) {
            restaurantesFrecuentes.add(restaurante);
        }
    }

    // Guarda los gustos de la persona
    public void agregarGusto(Plato plato, Restaurante restaurante) {
        Gusto nuevoGusto = new Gusto(plato, restaurante);
        this.gustos.add(nuevoGusto);
    }

    public void imprimirGustos() {
        System.out.println("Gustos de " + this.nombre + ":");
        if (gustos.isEmpty()) {
            System.out.println("No tiene platos favoritos registrados");
        }
        for (Gusto g : gustos) {
            System.out.println("Le encanta el plato " + g.getPlato().getNombre() +
                    " preparado en " + g.getRestaurante().getNombre());
        }
    }
}
